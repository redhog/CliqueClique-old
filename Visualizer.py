from __future__ import with_statement

import pydot, CliqueClique.Node

class VisualizerOperations(CliqueClique.Node.NodeOperations):
    node_color = "#999999"
    message_color = "#009900"
    message_link_color = "#559955"
    local_subscription_color = "#999999"
    remote_subscription_color = "#990000"
    id_cutoff = 4

    @classmethod
    def _id2label(cls, obj_id):
        obj_id = cls.id2s(obj_id)
        if cls.id_cutoff:
            obj_id = obj_id[-cls.id_cutoff:]
        return obj_id

    @classmethod
    def _ids2labels(cls, obj):
        # Note: Destructive method!
        for key in obj.keys():
            if key.endswith('_id'):
                obj[key] = cls._id2label(obj[key])
        return obj

    @classmethod
    def _ids2s(cls, obj):
        # Note: Destructive method!
        for key in obj.keys():
            if key.endswith('_id'):
                obj[key + '_l'] = cls._id2label(obj[key])
                obj[key] = cls.id2s(obj[key])
        return obj
    
class Visualizer(VisualizerOperations):
    def __init__(self):
        self.clear()
        
    def clear(self):
        self.clusters = {}
        self.graph = pydot.Dot("neato")
        self.graph.set_overlap("scale")

    def add_node(self, node, **kw):
        node_id = node.node_id
        self.clusters[self.id2s(node_id)] = pydot.Cluster(self.id2s(node_id), label='"%s"' % (self._id2label(node_id),), color = self.node_color, **kw)
        self.graph.add_subgraph(self.clusters[self.id2s(node_id)])
        with node._get_messages() as messages:
            for message in messages:
                with node._get_local_subscriptions(message_id = message['message_id']) as local_subscriptions:
                    local_subscription = list(local_subscriptions)
                if not local_subscription:
                    local_subscription = [{'is_subscribed': 'n/a', 'center_distance': 'n/a'}]
                self.add_message(node, message, local_subscription[0])
        with node._get_message_links() as message_links:
            for link in message_links:
                self.add_message_link(node, link)
        with node._get_subscriptions() as subscriptions:
            for subscription in subscriptions:
                self.add_subscription(node, subscription)
        
    def add_message(self, node, message, local_subscription, **kw):
        data = dict(message)
        data['node_id'] = node.node_id
        data.update(local_subscription)
        self._ids2s(data)
        self.clusters[self.id2s(node.node_id)].add_node(
            pydot.Node('"%(node_id)s/%(message_id)s"' % data,
                       label='"%(message_id_l)s: %(is_subscribed)s/%(center_distance)s->%(center_node_is_subscribed)s/%(center_node_id_l)s\\n%(content)s"' % data,
                       color=self.message_color,
                       **kw))

    def add_message_link(self, node, link, **kw):
        data = dict(link)
        data['node_id'] = node.node_id
        self._ids2s(data)
        self.graph.add_edge(
            pydot.Edge('"%(node_id)s/%(src_message_id)s"' % data,
                       '"%(node_id)s/%(dst_message_id)s"' % data,
                       color=self.message_link_color,
                       **kw))

    def add_subscription(self, node, subscription, **kw):
        data = dict(subscription)
        data['node_id'] = node.node_id
        self._ids2s(data)
        self.graph.add_edge(
            pydot.Edge('"%(node_id)s/%(message_id)s"' % data,
                       '"%(peer_id)s/%(message_id)s"' % data,
                       label='"L:%(local_is_subscribed)s/%(local_center_distance)s->%(local_center_node_is_subscribed)s/%(local_center_node_id_l)s R:%(remote_is_subscribed)s/%(remote_center_distance)s->%(remote_center_node_is_subscribed)s/%(remote_center_node_id_l)s"' % data,
                       color=self.remote_subscription_color,
                       **kw))
        
    def add_host(self, host):
        for node_id in host.get_nodes():
            node = host.get_node(node_id, cache=True)
            self.add_node(node)
