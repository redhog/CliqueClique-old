from __future__ import with_statement
import CliqueClique.Host, CliqueClique.Node, md5, unittest

class TestTypesystem(unittest.TestCase):
    @classmethod
    def node_num_to_id(cls, node_num):
        return md5.md5("node_%s" % node_num).hexdigest()

    def message_expr_test(self, expr, *messages):
        h = CliqueClique.Host.Host()
        n0 = h.get_node(CliqueClique.Node.NodeOperations.s2id(self.node_num_to_id(0)))

        with n0.get_messages_by_expr(expr) as res:
            found_messages = set(message['content'] for message in res)

        self.assertEqual(found_messages, set(messages))

    def test_typesystem_usage_basetype(self):
        self.message_expr_test(['and', ['system', 'usage'], ['basetypeis', ['system', 'type']]],
                               'usage')

    def test_typesystem_subtype_basetype(self):
        self.message_expr_test(['and', ['system', 'subtype'], ['basetypeis', ['system', 'usage']]],
                               'subtype')

    def test_typesystem_xml_basetype(self):
        self.message_expr_test(['and', ['system', 'xml'], ['basetypeis', ['system', 'text']]],
                               'xml')
