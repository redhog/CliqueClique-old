#! /usr/bin/python

import sqlite3, pdb, sys, traceback, pydot, subprocess, os, signal, md5
import Host
import Visualizer

class GthumbVisualizer(Visualizer.Visualizer):
    def __init__(self):
        Visualizer.Visualizer.__init__(self)
        self.filepath = "./test.png"
        self.graph.write_ps(self.filepath)
        self.viewer = subprocess.Popen(['gthumb', self.filepath])

    def write(self):
        self.graph.write_png(self.filepath)
#        os.kill(self.viewer.pid, signal.SIGHUP)

try:
    kws = dict([arg[2:].split('=', 1)
                for arg in sys.argv[1:]
                if arg.startswith('--') and '=' in arg])
    options = set([arg[2:]
                   for arg in sys.argv[1:]
                   if arg.startswith('--') and '=' not in arg])
    files = [arg
             for arg in sys.argv[1:]
             if not arg.startswith('--')]

    nr_of_nodes = int(kws['nodes'])

    graph = GthumbVisualizer()

    def node_num_to_id(node_num):
        return md5.md5("node_%s" % node_num).hexdigest()

    host = Host.Host()
    host.initialize()
    nodes = {}
    for node_num in xrange(0, nr_of_nodes):
        node_id = node_num_to_id(node_num)
        nodes[node_id] = host.get_node(node_id)
        nodes[node_id].commit()

    poster_node = nodes[node_num_to_id(0)]
    msg1 = poster_node.post_text_message('Message')
    msg2 = poster_node.post_text_message('Comment')
    msglnk1 = poster_node.post_link_message('Link', msg1, msg2)
    other_node = nodes[node_num_to_id(1)]
    other_node.import_message_from_peer(poster_node, msg1['message_id'])
    other_node.update_local_subscription(msg1)
    for node_num in xrange(0, nr_of_nodes):
        node_id = node_num_to_id(node_num)
        nodes[node_id].commit()
    other_node.sync_peers(poster_node)
#    while other_node.sync_peers(poster_node): pass

    for node_num in xrange(0, nr_of_nodes):
        node_id = node_num_to_id(node_num)
        nodes[node_id].commit()

    graph.add_host(host)
    graph.write()

except:
    traceback.print_exc()
    sys.last_traceback = sys.exc_info()[2]
    pdb.pm()
