from __future__ import with_statement

import Utils, Tables, datetime, md5, os.path

debug_delete_subscription = False
debug_delete_message = False
debug_message_id = False

class NodeOperations(object):
    @classmethod
    def id2s(cls, data_id):
        if data_id is None:
            return ""
        return hex(int(data_id))[2:-1]

    @classmethod
    def s2id(cls, data_id):
        if data_id == "":
            return None
        return int(data_id, 16)

    @classmethod
    def _calculate_data_id(cls, data):
        data_id = cls.s2id(md5.md5(data).hexdigest())
        if debug_message_id:
            print "Calculate data id:"
            print data
            print cls.id2s(data_id)
            print
        return data_id

    @classmethod
    def calculate_message_id(cls, message):
        return cls._calculate_data_id("%s:%s:%s" % (
            message.get('content', ''),
            cls.id2s(message.get('src_message_id', None)),
            cls.id2s(message.get('dst_message_id', None))))
    
    @classmethod
    def calculate_message_challenge_id(cls, message):
        return cls._calculate_data_id("challenge/%s" % (cls.id2s(cls.calculate_message_id(message)),))
        
    @classmethod
    def calculate_message_response_id(cls, node_id, message):
        return cls._calculate_data_id("challenge/%s/%s" % (cls.id2s(node_id),
                                                           cls.id2s(cls.calculate_message_id(message))))

class Node(NodeOperations):
    node_id = None
    
    def __init__(self, conn, node_id, **kw):
        self._conn = conn
        self.node_id = node_id
        if self.get_local_node() is None:
            self._initialize(**kw)
            self.commit()

    def _initialize(self, **kw):
        self._register_peer(
            Utils.subclass_dict(kw,
                                {'peer_id': self.node_id,
                                 'do_mirror': 1}))

    def _register_peer(self, peer):
        Tables.Peer.create_or_update(
            self._conn,
            Utils.subclass_dict(peer,
                                {'node_id': self.node_id,
                                 'last_seen_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}))

    def register_peer(self, peer):
        self._register_peer(
            Utils.subclass_dict(peer,
                                {'do_mirror': 0}))
    
    def get_peer(self, peer_id):
        return Tables.Peer.select_obj(self._conn, self.node_id, peer_id)

    def get_local_node(self):
        return Tables.Peer.select_obj(self._conn, self.node_id, self.node_id)

    def challenge_message(self, message_challenge_id):
        return Tables.Message.select_obj(
            self._conn, self.node_id, message_challenge_id = message_challenge_id
            )['message_response_id']

    def get_message(self, message_id):
        return Tables.Message.select_obj(self._conn, self.node_id, message_id)

    def _register_message(self, message):
        Tables.Message.create_or_update(
            self._conn,
            Utils.subclass_dict(message,
                                {'node_id': self.node_id,
                                 'message_response_id': self.calculate_message_response_id(self.node_id, message)}))

    def register_message(self, message, subscription):
        if message['message_id'] != subscription['message_id']:
            raise Exception("Subscription must be for message being registered")
        if (   int(message['message_id']) != self.calculate_message_id(message)
            or int(message['message_challenge_id']) != self.calculate_message_challenge_id(message)):
            raise Exception("Message id or challenge does not match message content (bad md5-sum!)")
        self._register_message(message)
        self.update_subscription(subscription)

    def update_subscription(self, subscription):
        if not self.get_message(subscription['message_id']):
            raise Exception("Message to subscribe, %s does not exist at peer %s" % (subscription['message_id'], self.node_id))
        Tables.Subscription.create_or_update(
            self._conn,
            Utils.subclass_dict(subscription,
                                {'node_id': self.node_id}))

    def delete_subscription(self, subscription):
        if debug_delete_subscription:
            print "Delete subscription: node=%s peer=%s message=%s" % (self.node_id, subscription['peer_id'], subscription['message_id'])
        Tables.Subscription.delete(
            self._conn,
            self.node_id,
            subscription['peer_id'],
            subscription['message_id'])
        other_subscription = Tables.Subscription.select_obj(self._conn, self.node_id, message_id=subscription['message_id'])
        if other_subscription is None:
            if debug_delete_message:
                print "Delete message: node=%s message=%s" % (self.node_id, subscription['message_id'])
            Tables.Message.delete(
                self._conn,
                self.node_id,
                subscription['message_id'])

    # Returns (subscription, message)
    def get_subscription_update(self, peer_id):
        update = Tables.SubscriptionUpdates.select_obj(self._conn, self.node_id, peer_id)

        if not update:
            return None, None, None

        if not update['delete_subscription'] is None:
            self.update_subscription(
                {'node_id': self.node_id,
                 'peer_id': peer_id,
                 'message_id': update['message_id'],
                 'local_is_subscribed': update['is_subscribed'],
                 'local_center_node_is_subscribed': update['center_node_is_subscribed'],
                 'local_center_node_id': update['center_node_id'],
                 'local_center_distance': update['center_distance']})
        
        local_subscription = Tables.Subscription.select_obj(self._conn, self.node_id, peer_id, update['message_id'])
        message = None
        if update['send_message']:
            message = Tables.Message.select_obj(self._conn, self.node_id, update['message_id'])

        subscription = dict(local_subscription)

        def swap_ids(d, id1, id2):
            d[id1], d[id2] = d[id2], d[id1]
        
        swap_ids(subscription, 'peer_id', 'node_id')
        swap_ids(subscription, 'remote_is_subscribed', 'local_is_subscribed')
        swap_ids(subscription, 'remote_center_node_is_subscribed', 'local_center_node_is_subscribed')
        swap_ids(subscription, 'remote_center_node_id', 'local_center_node_id')
        swap_ids(subscription, 'remote_center_distance', 'local_center_distance')

        if update['delete_subscription']:
            self.delete_subscription(local_subscription)

        return subscription, message, update['delete_subscription']
