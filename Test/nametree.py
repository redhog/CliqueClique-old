from __future__ import with_statement
import Host, md5, Node, Visualizer, unittest

class TestNametree(unittest.TestCase):
    @classmethod
    def node_num_to_id(cls, node_num):
        return md5.md5("node_%s" % node_num).hexdigest()

    def test_nametree(self):
        h = Host.Host()
        n0 = h.get_node(Node.NodeOperations.s2id(self.node_num_to_id(0)))

        for s in ('foobar', 'food', 'kafoo'):
            n0.post_direntrylink_message(
                n0.get_message_by_expr(["system", "rootdir"]),
                s,
                n0.post_text_message('entry:' + s))

        self.assertEqual(n0.get_message_by_expr(['nametreelookupentry', 'foobar', n0.get_message_by_expr(["system", "rootdir"])])['content'],
                         'entry:foobar')
