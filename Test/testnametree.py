from __future__ import with_statement
import Host, md5, Node, Visualizer

def node_num_to_id(node_num):
    return md5.md5("node_%s" % node_num).hexdigest()

h = Host.Host()
n0 = h.get_node(Node.NodeOperations.s2id(node_num_to_id(0)))

for s in ('foobar', 'food', 'kafoo'):
    print "ensure_nametree(%s)" % (s,)
    n0.ensure_nametree(n0.get_message_by_expr(["system", "rootdir"]), s)

with n0.get_messages_by_expr(['nametreelinked', ['content', 'f'], []]) as x:
    for y in x:
        print Visualizer.Visualizer._ids2s(y)
