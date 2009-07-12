import pydot

class Visualizer(object):
    node_color = "#999999"
    message_color = "#009900"
    message_link_color = "#559955"
    local_subscription_color = "#999999"
    remote_subscription_color = "#990000"
    
    def __init__(self):
        self.clear()
        
    def clear(self):
        self.clusters = {}
        self.graph = pydot.Dot("neato")
        self.graph.set_overlap("scale")

    def add_node(self, node, **kw):
        node_id = node.node_id
        self.clusters[node_id] = pydot.Cluster(node_id, label=node_id, color = self.node_color, **kw)
        self.graph.add_subgraph(self.clusters[node_id])
        for message in node._get_messages():
            local_subscription = list(node._get_local_subscriptions(message_id = message['message_id']))
            if not local_subscription:
                local_subscription = [{'is_subscribed': 'n/a', 'center_distance': 'n/a'}]
            self.add_message(node, message, local_subscription[0])
        for link in node._get_message_links():
            self.add_message_link(node, link)
        for subscription in node._get_subscriptions():
            self.add_subscription(node, subscription)
        
    def add_message(self, node, message, local_subscription, **kw):
        node_id = node.node_id
        message_id = message['message_id']
        label_data = dict(message)
        label_data.update(local_subscription)
        label = '"%(message_id)s: %(is_subscribed)s[%(center_distance)s]\\n%(content)s"' % label_data
        self.clusters[node_id].add_node(pydot.Node(node_id + "/" + message_id, label=label, color = self.message_color, **kw))

    def add_message_link(self, node, link, **kw):
        node_id = node.node_id
        src_message_id = link['src_message_id']
        dst_message_id = link['dst_message_id']
        self.graph.add_edge(pydot.Edge(node_id + "/" + src_message_id, node_id + "/" + dst_message_id, color=self.message_link_color, **kw))

    def add_subscription(self, node, subscription, **kw):
        node1_id = node.node_id
        message_id = subscription['message_id']
        node2_id = subscription['peer_id']
        label = '"L:%(local_is_subscribed)s[%(local_center_distance)s] R:%(remote_is_subscribed)s[%(remote_center_distance)s]"' % subscription
        self.graph.add_edge(pydot.Edge(node1_id + "/" + message_id, node2_id + "/" + message_id, label = label, color=self.remote_subscription_color, **kw))
        
    def add_host(self, host):
        for node_id in host.get_nodes():
            self.add_node(host.get_node(node_id))
