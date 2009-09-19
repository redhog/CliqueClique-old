from __future__ import with_statement

import ExprNode, Tables

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
