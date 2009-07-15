from __future__ import with_statement

import Utils, Tables, datetime, md5, os.path

debug_delete_subscription = True
debug_delete_message = True

class NodeOperations(object):
    @classmethod
    def _calculate_message_id(cls, salt, message):
        return md5.md5(salt + repr((message.get('content', None),
                                    message.get('src_message_id', None),
                                    message.get('dst_message_id', None)))
                       ).hexdigest()

    @classmethod
    def calculate_message_id(cls, message):
        return cls._calculate_message_id('id', message)
        
    @classmethod
    def calculate_message_challenge(cls, message):
        return cls._calculate_message_id('challenge', message)
        
    @classmethod
    def calculate_message_response(cls, node_id, message):
        return cls._calculate_message_id('response' + node_id, message)

class Node(NodeOperations):
    def __init__(self, conn, node_id, host):
        self.conn = conn
        self.node_id = node_id
        self.host = host
        if self.get_local_node() is None:
            self._initialize()

    def _initialize(self):
        self._register_peer({'peer_id': self.node_id,
                             'do_mirror': 1})

    def _register_peer(self, peer):
        Tables.Peer.create_or_update(
            self.conn,
            Utils.subclass_dict(peer,
                                {'node_id': self.node_id,
                                 'last_seen_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}))

    def register_peer(self, peer):
        self._register_peer(
            Utils.subclass_dict(peer,
                                {'do_mirror': 0}))
    
    def get_peer(self, peer_id):
        return Tables.Peer.select_obj(self.conn, self.node_id, peer_id)

    def get_local_node(self):
        return Tables.Peer.select_obj(self.conn, self.node_id, self.node_id)

    def challenge_message(self, message_challenge):
        return Tables.Message.select_obj(
            self.conn, self.node_id, message_challenge = message_challenge
            )['message_response']

    def get_message(self, message_id):
        return Tables.Message.select_obj(self.conn, self.node_id, message_id)

    def _register_message(self, message):
        Tables.Message.create_or_update(
            self.conn,
            Utils.subclass_dict(message,
                                {'node_id': self.node_id,
                                 'message_response': self.calculate_message_response(self.node_id, message)}))

    def register_message(self, message, subscription):
        if message['message_id'] != subscription['message_id']:
            raise Exception("Subscription must be for message being registered")
        if (   message['message_id'] != self.calculate_message_id(message)
            or message['message_challenge'] != self.calculate_message_challenge(message)):
            raise Exception("Message id or challenge does not match message content (bad md5-sum!)")
        self._register_message(message)
        self.update_subscription(subscription)

    def update_subscription(self, subscription):
        if not self.get_message(subscription['message_id']):
            raise Exception("Message to subscribe, %s does not exist at peer %s" % (subscription['message_id'], self.node_id))
        Tables.Subscription.create_or_update(
            self.conn,
            Utils.subclass_dict(subscription,
                                {'node_id': self.node_id}))

    def delete_subscription(self, subscription):
        if debug_delete_subscription:
            print "Delete subscription: node=%s peer=%s message=%s" % (self.node_id, subscription['peer_id'], subscription['message_id'])
        Tables.Subscription.delete(
            self.conn,
            self.node_id,
            subscription['peer_id'],
            subscription['message_id'])
        other_subscription = Tables.Subscription.select_obj(self.conn, self.node_id, message_id=subscription['message_id'])
        if other_subscription is None:
            if debug_delete_message:
                print "Delete message: node=%s message=%s" % (self.node_id, subscription['message_id'])
            Tables.Message.delete(
                self.conn,
                self.node_id,
                subscription['message_id'])

    # Returns (subscription, message)
    def get_subscription_update(self, peer_id):
        update = Tables.SubscriptionUpdates.select_obj(self.conn, self.node_id, peer_id)

        if not update:
            return None, None, None

        if not update['delete_subscription'] is None:
            self.update_subscription(
                {'node_id': self.node_id,
                 'peer_id': peer_id,
                 'message_id': update['message_id'],
                 'local_is_subscribed': update['is_subscribed'],
                 'local_center_distance': update['center_distance']})
        
        local_subscription = Tables.Subscription.select_obj(self.conn, self.node_id, peer_id, update['message_id'])
        message = None
        if update['send_message']:
            message = Tables.Message.select_obj(self.conn, self.node_id, update['message_id'])

        subscription = dict(local_subscription)
        subscription['peer_id'], subscription['node_id'] = subscription['node_id'], subscription['peer_id']
        subscription['remote_is_subscribed'], subscription['local_is_subscribed'] = subscription['local_is_subscribed'], subscription['remote_is_subscribed']
        subscription['remote_center_distance'], subscription['local_center_distance'] = subscription['local_center_distance'], subscription['remote_center_distance']

        if update['delete_subscription']:
            self.delete_subscription(local_subscription)

        return subscription, message, update['delete_subscription']

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
