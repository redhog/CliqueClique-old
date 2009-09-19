from __future__ import with_statement

import Node, Tables

class IntrospectionNode(Node.Node):
    def _get_messages(self, **kw):
        return Tables.Message.select_objs(self._conn, node_id = self.get_local_node()['node_id'], **kw)

    def _get_local_subscriptions(self, **kw):
        return Tables.LocalSubscription.select_objs(self._conn, node_id = self.get_local_node()['node_id'], **kw)

    def _get_subscriptions(self, **kw):
        return Tables.Subscription.select_objs(self._conn, node_id = self.get_local_node()['node_id'], **kw)

    def _get_message_links(self, **kw):
        return Tables.MessageLink.select_objs(self._conn, node_id = self.get_local_node()['node_id'], **kw)
    
