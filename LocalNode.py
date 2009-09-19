from __future__ import with_statement

import datetime, md5, threading, operator, types, socket
import ExprNode, SyncNode, Utils, Tables, Node, Visualizer
import symmetricjsonrpc
import traceback


class IntrospectionNode(Node.Node):
    def _get_messages(self, **kw):
        return Tables.Message.select_objs(self._conn, node_id = self.get_local_node()['node_id'], **kw)

    def _get_local_subscriptions(self, **kw):
        return Tables.LocalSubscription.select_objs(self._conn, node_id = self.get_local_node()['node_id'], **kw)

    def _get_subscriptions(self, **kw):
        return Tables.Subscription.select_objs(self._conn, node_id = self.get_local_node()['node_id'], **kw)

    def _get_message_links(self, **kw):
        return Tables.MessageLink.select_objs(self._conn, node_id = self.get_local_node()['node_id'], **kw)
    
class SubscriptionNode(ExprNode.ExprNode):
    def update_local_subscription(self, message, subscribed = 1):
        subscription = Tables.Subscription.select_obj(self._conn, node_id = self.get_local_node()['node_id'], peer_id = self.get_local_node()['node_id'], message_id = message['message_id'])
        if subscription is None:
            subscription = {'peer_id': self.get_local_node()['node_id'],
                            'message_id': message['message_id'],
                            'local_is_subscribed': 1,
                            'local_center_node_is_subscribed': 1,
                            'local_center_node_id': self.get_local_node()['node_id'],
                            'local_center_distance': 1,
                            'remote_is_subscribed': 1,
                            'remote_center_node_is_subscribed': 1,
                            'remote_center_node_id': self.get_local_node()['node_id'],
                            'remote_center_distance': 0}
        subscription['remote_is_subscribed'] = subscribed
        subscription['remote_center_node_is_subscribed'] = subscribed
        self.update_subscription(subscription)

    def delete_local_subscription(self, message):
        subscription = Tables.Subscription.select_obj(self._conn, node_id = self.get_local_node()['node_id'], peer_id = self.get_local_node()['node_id'], message_id = message['message_id'])
        if subscription is not None:
            self.delete_subscription(subscription)

class AnnotationNode(Node.Node):
    def set_annotation(self, name, value, message = None, peer = None):
        Tables.Annotation.create_or_update(
            self._conn,
            {'node_id': self.node_id,
             'name': name,
             'message_id': message and message['message_id'] or None,
             'peer_id': peer and peer['peer_id'] or None,
             'value': value})
        
    def get_annotation(self, name, message = None, peer = None):
        return Tables.Annotation.select_obj(
            self._conn, self.node_id,
            name,
            message and message['message_id'] or None,
            peer and peer['peer_id'] or None)['value']


class PostingNode(SubscriptionNode, AnnotationNode):
    def post_message(self, message):
        message['message_id'] = self.calculate_message_id(message)
        message['message_challenge_id'] = self.calculate_message_challenge_id(message)
        self._register_message(message)
        self.update_local_subscription(message)
        return message

    def post_text_message(self, content):
        return self.post_message({'content': content})

    def post_link_message(self, link_description, src_message, dst_message):
        return self.post_message({'content': link_description,
                                  'src_message_id': src_message['message_id'],
                                  'dst_message_id': dst_message['message_id']})

    def post_usagelink_message(self, message, usage):
        return self.post_link_message(
            'linkisusage',
            self.post_link_message('usagelink', message, usage),
            self.get_message_by_expr(["system", "usage"]))

    def post_usaged_link_message(self, link_description, src_message, dst_message, usage):
        link = self.post_link_message(link_description, src_message, dst_message)
        self.post_usagelink_message(link, usage)
        return link

    def post_typelink_message(self, message, type):
        return self.post_usagelink_message(
            self.post_link_message('typelink', message, type),
            self.get_message_by_expr(["system", "type"]))

    def post_typed_text_message(self, content, type):
        message = self.post_text_message(content)
        self.post_typelink_message(message, type)
        return message

    def post_subtypelink_message(self, type, parent_type):
        return self.post_usaged_link_message(
            'subtypelink', type, parent_type,
            self.get_message_by_expr(["system", "subtype"]))

    def post_nametreelink_message(self, parent, char, child):
        return self.post_usaged_link_message(
            char, parent, child,
            self.get_message_by_expr(["system", "nametreelink"]))

    def post_nametreenode_message(self, root, name):
        return self.post_typed_text_message(
            'nametreenode:%s:%s' % (isinstance(root, dict) and self.id2s(root['message_id']) or root, name),
            self.get_message_by_expr(["system", "nametreenode"]))

    def post_nametreeroot_message(self, parent_root):
        return self.post_nametreenode_message(parent_root, '')

    def post_nametreeleaflink_message(self, nametreenode, message):
        return self.post_usaged_link_message(
            'nametreeleaflink', nametreenode, message,
            self.get_message_by_expr(["system", "nametreeleaflink"]))

    def post_nametreelevel_message(self, root, name, existing, char):
        node = self.post_nametreenode_message(root, name)
        self.post_nametreelink_message(existing, char, node),
        return node

    def get_existing_nametree_prefix(self, root, name):
        #FIXME: Use binary search here to speed things up!
        existing_name = name
        node = self.get_message_by_expr(["nametreelookup", existing_name, root])
        while not node and existing_name:
            existing_name = existing_name[:-1]
            node = self.get_message_by_expr(["nametreelookup", existing_name, root])
        return node or root, name[len(existing_name):]
        
    def ensure_nametree(self, root, name):
        existing, rest_name = self.get_existing_nametree_prefix(root, name)
        self.update_local_subscription(existing)
        prefix = name[:-len(rest_name)]
        for char in rest_name:
            prefix = prefix + char
            existing = self.post_nametreelevel_message(root, prefix, existing, char)
        return existing

    def post_direntrylink_message(self, root, name, message):
        return self.post_nametreeleaflink_message(self.ensure_nametree(root, name), message)        
    
class LocalNode(SyncNode.ThreadSyncNode, IntrospectionNode, PostingNode):
    pass
