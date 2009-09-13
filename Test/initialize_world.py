from __future__ import with_statement
import Host, md5, Node, Visualizer

def node_num_to_id(node_num):
    return md5.md5("node_%s" % node_num).hexdigest()

h = Host.Host()
h.initialize()
n0 = h.get_node(Node.NodeOperations.s2id(node_num_to_id(0)))

def setanno(n, name, message):
    n.set_annotation("global_attribute_cache", "/system/%s" % name, message)
    return message

def create(n, name):
    return setanno(n, name, n.post_text_message(name))

def createtyped(n, name, type):
    return setanno(n, name, n.post_typed_text_message(name, type))

def createtype(n, name, parent):
    res = createtyped(n, name, n.get_message_by_expr(["system", "type"]))
    n.post_subtypelink_message(res, parent)
    return res


create(n0, 'usage')
create(n0, 'type')
create(n0, 'subtype')

n0.post_typelink_message(n0.get_message_by_expr(["system", "type"]),
                         n0.get_message_by_expr(["system", "type"]))
n0.post_typelink_message(n0.get_message_by_expr(["system", "usage"]),
                         n0.get_message_by_expr(["system", "type"]))
n0.post_typelink_message(n0.get_message_by_expr(["system", "subtype"]),
                         n0.get_message_by_expr(["system", "type"]))

n0.post_subtypelink_message(n0.get_message_by_expr(["system", "usage"]),
                            n0.get_message_by_expr(["system", "type"]))
n0.post_subtypelink_message(n0.get_message_by_expr(["system", "subtype"]),
                            n0.get_message_by_expr(["system", "usage"]))

createtype(n0, 'nametreelink', n0.get_message_by_expr(["system", "usage"]))
createtype(n0, 'nametreenode', n0.get_message_by_expr(["system", "type"]))
createtype(n0, 'nametreeleaflink', n0.get_message_by_expr(["system", "usage"]))

createtype(n0, 'text', n0.get_message_by_expr(["system", "type"]))
createtype(n0, 'xml', n0.get_message_by_expr(["system", "text"]))
createtype(n0, 'xhtml', n0.get_message_by_expr(["system", "xml"]))
createtype(n0, 'css', n0.get_message_by_expr(["system", "text"]))

setanno(n0, 'rootdir', n0.post_nametreeroot_message('root'))

n0.commit()
