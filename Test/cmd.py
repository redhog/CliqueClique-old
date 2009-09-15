from __future__ import with_statement
import Host, Node, Visualizer
import sys


def parse_argv(argv):
    kws = {}
    for arg in argv:
        if arg.startswith('--') and '=' in arg:
            key, value = arg[2:].split('=', 1)
            if key not in kws:
                kws[key] = []
            kws[key].append(value)
    options = set([arg[2:]
                   for arg in sys.argv[1:]
                   if arg.startswith('--') and '=' not in arg])
    files = [arg
             for arg in sys.argv[1:]
             if not arg.startswith('--')]
    return kws, options, files


kws, options, files = parse_argv(sys.argv[1:])

h = Host.Host()
n = h.get_node(Node.NodeOperations.s2id(kws['node'][0]))

if 'post' in kws:
    path, value = kws['post'][0].split('=', 1)
    n.post_pathentry_message(n.get_message_by_expr(['system', 'rootdir']),
                             path.split('/')[1:],
                             n.post_text_message(value))
    n.commit()                             
if 'list' in kws:
    dir = ["cd", kws['list'][0].split('/')[1:], ['system', 'rootdir']]
    with n.get_messages_by_expr(["dirlinked", [], dir]) as x:
        print "Continuations: %s" % (', '.join(m['content'] for m in x),)
    
    dir = ["cd", kws['list'][0][1:].split('/'), ['system', 'rootdir']]
    print "Content:"
    with n.get_messages_by_expr(["dircontentlinked", [], dir]) as x:
        for m in x:
            print "    ", Visualizer.VisualizerOperations._ids2labels(m)
