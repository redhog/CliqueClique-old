from __future__ import with_statement

import datetime, md5, threading
import Utils, Tables, Node


class SyncNode(Node.Node):
    def sync_peers_locally(self, other):
        return self.sync_self() + other.sync_self() + self.sync_peers(other)

    def sync_peers(self, other):
        return self.sync_peer(other, True) + self.sync_peer(other, False)

    def sync_peer(self, other, send = True):
        if not send:
            self, other = other, self

        subscription, message, delete_subscription = self.get_subscription_update(other.node_id)
        print "%s -> %s : %s, %s, delete:%s" % (self.node_id, other.node_id, subscription, message, delete_subscription)
        if subscription:
            if delete_subscription:
                other.delete_subscription(subscription)
            else:
                # Yes, ignore result if syncing self, just pretend we did an update
                if self.node_id != other.node_id:
                    if message:
                        other.register_message(message, subscription)
                    else:
                        other.update_subscription(subscription)
            return 1
        return 0

    def sync_self(self):
        return self.sync_peer(self)

    def connect_peers(self, other):
        for peers in Utils.bidirectional(self, other):
            peers[0].register_peer(peers[1].get_local_node())

    def import_message_from_peer(self, other, message_id):
        self.connect_peers(other)
        message = other.get_message(message_id)
        self.register_message(
            message,
            {'peer_id': other.node_id,
             'message_id': message['message_id']})
        self.update_local_subscription(message, 0)

    def get_peers(self):
        return [obj['peer_id']
                for obj in Tables.Peer.select_objs_sql(self.conn, self.node_id)]

    def get_peer(self, peer_id):
        # Add XMLL-RPC connect interface here...
        self.host.get_node(peer_id)

class ThreadSyncNode(SyncNode):
    def __init__(self, *arg, **kw):
        self.new_sync_event = threading.Condition()
        self.shutdown_sync_threads = [] # List of peer_ids or True 
        super(ThreadSyncNode, self).__init__(*arg, **kw)

    class SyncThread(threading.Thread):
        def __init__(self, node, peer, *arg, **kw):
            self.node = node
            self.peer = peer
            threading.Thread.__init__(
                self, name = "SyncThread @ %s for %s" % (node.node_id, peer.node_id), *arg, **kw)

        def sync():
            return self.node.sync_peer(self.node.peer)

        def lifecontrol():
            return (    self.node.shutdown_sync_threads is not True
                    and self.peer.node_id not in self.node.shutdown_sync_threads)

        def run(self):
            while self.lifecontrol():
                while self.lifecontrol() and self.sync():
                    self.node.new_sync_event.notifyAll()
            self.node.new_sync_event.wait()


class IntrospectionNode(Node.Node):
    def _get_messages(self, **kw):
        return Tables.Message.select_objs(self.conn, node_id = self.node_id, **kw)

    def _get_local_subscriptions(self, **kw):
        return Tables.LocalSubscription.select_objs(self.conn, node_id = self.node_id, **kw)

    def _get_subscriptions(self, **kw):
        return Tables.Subscription.select_objs(self.conn, node_id = self.node_id, **kw)

    def _get_message_links(self, **kw):
        return Tables.MessageLink.select_objs(self.conn, node_id = self.node_id, **kw)


class UINode(Node.Node):
    def post_message(self, message):
        message['message_id'] = self.calculate_message_id(message)
        message['message_challenge'] = self.calculate_message_challenge(message)
        self._register_message(message)
        self.update_subscription({'peer_id': self.node_id,
                                  'message_id': message['message_id'],
                                  'local_is_subscribed': 1,
                                  'local_center_distance': 1,

                                  'remote_is_subscribed': 1,
                                  'remote_center_distance': 0})
        return message

    def update_local_subscription(self, message, subscribed = 1):
        subscription = Tables.Subscription.select_obj(self.conn, node_id = self.node_id, peer_id = self.node_id, message_id = message['message_id'])
        if subscription is None:
            subscription = {'peer_id': self.node_id,
                            'message_id': message['message_id'],
                            'local_is_subscribed': 1}
        subscription['remote_is_subscribed'] = subscribed
        self.update_subscription(subscription)

    def delete_local_subscription(self, message):
        subscription = Tables.Subscription.select_obj(self.conn, node_id = self.node_id, peer_id = self.node_id, message_id = message['message_id'])
        if subscription is not None:
            self.delete_subscription(subscription)

    def post_text_message(self, content):
        return self.post_message({'content': content})

    def post_link_message(self, link_description, src_message, dst_message):
        return self.post_message({'content': link_description,
                                  'src_message_id': src_message['message_id'],
                                  'dst_message_id': dst_message['message_id']})


class LocalNode(ThreadSyncNode, IntrospectionNode, UINode):
    pass
