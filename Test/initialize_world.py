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

create(n0, 'usage')
def setusage(n, m, u):
    return n.post_link_message(
        'linkisusage', n.post_link_message('usagelink', m, u),
        n.get_message_by_expr(["system", "usage"]))

create(n0, 'type')
def settype(n, m, t):
    setusage(
        n,
        n.post_link_message('typelink', m, t),
        n.get_message_by_expr(["system", "type"]))
settype(
    n0,
    n0.get_message_by_expr(["system", "type"]),
    n0.get_message_by_expr(["system", "type"]))

create(n0, 'subtype')
def setsubtype(n, t, p):
    setusage(
        n,
        n.post_link_message('subtypelink', t, p),
        n.get_message_by_expr(["system", "subtype"]))

def createtype(n, name, parent):
    res = create(n, name)
    settype(n, res, n.get_message_by_expr(["system", "type"]))
    setsubtype(n, res, parent)
    return res

createtype(n0, 'text', n0.get_message_by_expr(["system", "type"]))
createtype(n0, 'xml', n0.get_message_by_expr(["system", "text"]))
createtype(n0, 'xhtml', n0.get_message_by_expr(["system", "xml"]))
createtype(n0, 'css', n0.get_message_by_expr(["system", "text"]))

n0.commit()
