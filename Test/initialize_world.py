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

musage = create(n0, 'usage')
def setusage(n, m, u):
    return n.post_link_message(
        'linkisusage', n.post_link_message('usagelink', m, u), musage)

mtype = create(n0, 'type')
def settype(n, m, t):
    setusage(
        n,
        n.post_link_message('typelink', m, t),
        mtype)
settype(n0, mtype, mtype)

msubtype = create(n0, 'subtype')
def setsubtype(n, t, p):
    setusage(
        n,
        n.post_link_message('subtypelink', t, p),
        msubtype)

def createtype(n, name, parent):
    res = create(n, name)
    settype(n, res, mtype)
    setsubtype(n, res, parent)
    return res

mtypetext = createtype(n0, 'text', mtype)
mtypexml = createtype(n0, 'xml', mtypetext)
mtypexhtml = createtype(n0, 'xhtml', mtypexml)
mtypecss = createtype(n0, 'css', mtypetext)

n0.commit()
