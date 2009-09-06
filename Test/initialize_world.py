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


musage = create(n, 'usage')

def setusage(n, m, u):
    return n.post_link_message(
        '', n.post_link_message('', m, u), musage)

mtype = create(n, 'type')

def settype(n, m, t):
    setusage(
        n0.post_link_message('', m, t),
        mtype)

settype(mtype, mtype)

msubtype = create(n, 'subtype')
settype(msubtype, mtype)


mtypetext = create('text')
settype(mtypetext, mtype)

mtypehtml = create('html')
settype(mtypetext, mtype)


n0.post_link_message('',
                     n0.post_link_message('',
                                          n0.post_link_message('',
                                                               mtype,
                                                               mtypetext),
                                          msubtype),
                     mtype)


mtypetype = n0.post_link_message('Type of Type is Type', mtype, mtype)
mtypetypetype = n0.post_link_message('Usage of link: message type', mtypetype, musage)




m2 = n0.post_text_message('Comment')
m3 = n0.post_link_message('Link', m1, m2)

n0.set_annotation("foo", "bar", m1)

n0.commit()

print n0.get_annotation("foo", m1)
