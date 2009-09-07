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
        '', n.post_link_message('', m, u), musage)

mtype = create(n0, 'type')
def settype(n, m, t):
    setusage(
        n,
        n.post_link_message('', m, t),
        mtype)
settype(n0, mtype, mtype)

msubtype = create(n0, 'subtype')
def setsubtype(n, t, p):
    setusage(
        n,
        n.post_link_message('', t, p),
        msubtype)

settype(n0, mtypetext, mtype)
setsubtype(n0, mtypetext, mtype):

mtypetext = create(n0, 'text')
settype(n0, mtypetext, mtype)
setsubtype(n0, mtypetext, mtype):

mtypehtml = create(n0, 'html')
settype(n0, mtypehtml, mtype)
setsubtype(n0, mtypehtml, mtypetext):


m2 = n0.post_text_message('Comment')
m3 = n0.post_link_message('Link', m1, m2)

n0.set_annotation("foo", "bar", m1)

n0.commit()

print n0.get_annotation("foo", m1)
