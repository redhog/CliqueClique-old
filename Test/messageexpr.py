from __future__ import with_statement
import Host, md5, Node, Visualizer
def node_num_to_id(node_num):
    return md5.md5("node_%s" % node_num).hexdigest()

h = Host.Host()
n0 = h.get_node(Node.NodeOperations.s2id(node_num_to_id(0)))

with n0.get_messages_by_expr(["linksto", ["linksto", ["id", n0.s2id("4d601bc8587ddbf7e86cb0bbfdefa4f4")]]]) as x:
    for m in x:
        print Visualizer.VisualizerOperations._ids2labels(m)
