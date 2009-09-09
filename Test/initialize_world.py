from __future__ import with_statement
import Host, md5, Node, Visualizer

def node_num_to_id(node_num):
    return md5.md5("node_%s" % node_num).hexdigest()

h = Host.Host()
h.initialize()
n0 = h.get_node(Node.NodeOperations.s2id(node_num_to_id(0)))

def create(n, name):
    res = n.post_text_message(name)
    n.set_annotation("global_attribute_cache", "/system/%s" % name, res)
    return res

def createtype(n, name, parent):
    res = create(n, name)
    n.post_typelink_message(res, n.get_message_by_expr(["system", "type"]))
    n.post_subtypelink_message(res, n.get_message_by_expr(["system", "type"]))
    return res


create(n0, 'usage')
create(n0, 'type')
n0.post_typelink_message(n0.get_message_by_expr(["system", "type"]), n0.get_message_by_expr(["system", "type"]))
create(n0, 'subtype')
createtype(n0, 'text', n0.get_message_by_expr(["system", "type"]))
createtype(n0, 'xml', n0.get_message_by_expr(["system", "text"]))
createtype(n0, 'xhtml', n0.get_message_by_expr(["system", "xml"]))
createtype(n0, 'css', n0.get_message_by_expr(["system", "text"]))

n0.commit()
