import Table

class Peer(Table.Table):
    table_name = 'peer'
    id_cols = ('node_id', 'peer_id',)
   
class Subscription(Table.Table):
    table_name = 'subscription'
    id_cols = ('node_id', 'peer_id', 'message_id')
   
class Message(Table.Table):
    table_name = 'message'
    id_cols = ('node_id', 'message_id',)

class SubscriptionUpdates(Table.Table):
    table_name = 'subscription_updates'
    id_cols = ('node_id', 'peer_id','message_id')

class MessageLink(Table.Table):
    table_name = 'message_link'
    id_cols = ('node_id', 'src_message_id', 'dst_message_id')

class UpstreamSubscription(Table.Table):
    table_name = "upstream_subscription"
    id_cols = ('node_id', 'message_id', "peer_id")

class DownstreamSubscription(Table.Table):
    table_name = "downstream_subscription"
    id_cols = ('node_id', 'message_id', "peer_id")

class LocalSubscription(Table.Table):
    table_name = "full_recursive_local_subscription"
    id_cols = ('node_id', 'message_id')

