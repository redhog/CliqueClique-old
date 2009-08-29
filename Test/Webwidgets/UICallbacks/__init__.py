#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=UTF-8 :

# Webwidgets web developement framework
# Copyright (C) 2007 FreeCode AS, Egil Moeller <egil.moeller@freecode.no>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
from __future__ import with_statement

import pydot
import Webwidgets
import md5
import CliqueClique.Host, CliqueClique.Node, CliqueClique.Visualizer, CliqueClique.Tables

def node_num_to_id(node_num):
    return md5.md5("node_%s" % node_num).hexdigest()

debug_graphviz = False

def add_to_tree(tree, path, value):
    for item in path[:-1]:
        if item not in tree:
            tree[item] = {}
        tree = tree[item]
    tree[path[-1]] = value

class MainWindow(object):
    class Body(object):
        def __init__(self, *arg, **kw):
            Webwidgets.Html.__init__(self, *arg, **kw)
            self.host = CliqueClique.Host.Host()
            
        class Graph(CliqueClique.Visualizer.Visualizer):
            def __init__(self, *arg, **kw):
                Webwidgets.DotGraph.__init__(self, *arg, **kw)
                CliqueClique.Visualizer.Visualizer.__init__(self)

            def output(self, output_options):
                try:
                    return Webwidgets.DotGraph.output(self, output_options)
                finally:
                    if debug_graphviz:
                        print "=========================================="
                        print self.graph.create(format = 'dot')
                        print "=========================================="

            def get_node(self, node_id):
                return self.parent.host.get_node(self.s2id(node_id), True)

            def get_node_message(self, message):
                node_id, message_id = message.split(':')
                node = self.get_node(node_id)
                return node, node.get_message(self.s2id(message_id))

            def get_message(self, message):
                return self.get_node_message(message)[1]


            def update(self):
                self.clear()
                self.add_host(self.parent.host)

            def add_node(self, node, **kw):
                if node.id2s(node.node_id) in (self + "1:Params-Nodes-Field").value: 
                    kw['style'] = 'filled'
                    kw['fillcolor'] = self.node_color
                CliqueClique.Visualizer.Visualizer.add_node(
                    self, node, URL = self.calculate_callback_url('node:%s' % (node.id2s(node.node_id),)), **kw)

            def add_message(self, node, message, local_subscription, **kw):
                id_name = '%s:%s' % (node.id2s(node.node_id),
                                     node.id2s(message['message_id']))
                if id_name in (self + "1:Params-Messages-Field").value:
                    kw['style'] = 'filled'
                    kw['fillcolor'] = self.message_color
                CliqueClique.Visualizer.Visualizer.add_message(
                    self, node, message, local_subscription,
                    URL = self.calculate_callback_url('message:' + id_name),
                    **kw)
                
            def add_message_link(self, node, link, **kw):
                CliqueClique.Visualizer.Visualizer.add_message_link(
                    self, node, link,
                    **kw)
                
            def add_subscription(self, node, subscription, **kw):
                id_name = '%s:%s:%s' % (node.id2s(node.node_id),
                                        node.id2s(subscription['message_id']),
                                        node.id2s(subscription['peer_id']))
                if id_name in (self + "1:Params-Subscriptions-Field").value: 
                    kw['labelfontcolor'] = self.remote_subscription_color
                CliqueClique.Visualizer.Visualizer.add_subscription(
                    self, node, subscription,
                    URL = self.calculate_callback_url('subscription:' + id_name),
                    **kw)

            def selected(self, path, selection):
                head, tail = selection.split(':', 1)
                if head == 'node':
                    field = self + "1:Params-Nodes-Field"
                elif head == 'message':
                    field = self + "1:Params-Messages-Field"
                elif head == 'subscription':
                    field = self + "1:Params-Subscriptions-Field"
                else:
                    print "OUPS"
                    return
                values = field.value.strip().split(' ')
                if tail in values:
                    values.remove(tail)
                else:
                    values.append(tail)
                field.value = ' '.join(values)
                self.update()
                
        class Ops(object):
            class Update(object):
                def clicked(self, path):
                    (self + "2:Graph").update()

            class SyncSelf(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    for node in nodes:
                        node = graph.get_node(node)
                        node.sync_self()
                        node.commit()
                    (self + "2:Graph").update()
            class Sync(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node1 = graph.get_node(nodes[0])
                    node2 = graph.get_node(nodes[1])
                    node1.sync_peer(node2)
                    node1.commit()
                    node2.commit()
                    (self + "2:Graph").update()
            class RevSync(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node1 = graph.get_node(nodes[0])
                    node2 = graph.get_node(nodes[1])
                    node2.sync_peer(node1)
                    node1.commit()
                    node2.commit()
                    (self + "2:Graph").update()
            class SyncBoth(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node1 = graph.get_node(nodes[0])
                    node2 = graph.get_node(nodes[1])
                    node2.sync_peers(node1)
                    node1.commit()
                    node2.commit()
                    (self + "2:Graph").update()
            class SyncAll(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node1 = graph.get_node(nodes[0])
                    node2 = graph.get_node(nodes[1])
                    while node2.sync_peers_locally(node1): pass
                    node1.commit()
                    node2.commit()
                    (self + "2:Graph").update()

            class StartThreadSync(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    for node in nodes:
                        node = graph.get_node(node)
                        node.sync_start()
                    (self + "2:Graph").update()

            class StopThreadSync(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    for node in nodes:
                        node = graph.get_node(node)
                        node.sync_stop()
                    (self + "2:Graph").update()
                    
            class PokeThreadSync(object):
                def clicked(self, path):
                    body = self + "2:"
                    body.host.signal_change()
                    (self + "2:Graph").update()
                    
            class Initialize(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    (self+"2:").host.initialize()
                    poster_node = graph.get_node(node_num_to_id(0))
                    msg = poster_node.post_text_message('Root message')
                    other_node = graph.get_node(node_num_to_id(1))
                    other_node.import_message_from_peer(poster_node, msg['message_id'])
                    poster_node.commit()
                    other_node.commit()
                    (self + "2:Graph").update()

            class CreateTestData(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    (self+"2:").host.initialize()
                    nodes = [graph.get_node(node_num_to_id(x)) for x in xrange(0, 3)]

                    msg1 = nodes[0].post_text_message('Message')
                    msg2 = nodes[0].post_text_message('Comment')
                    msglnk1 = nodes[0].post_link_message('Link', msg1, msg2)
                    
                    nodes[1].import_message_from_peer(nodes[0], msg1['message_id'])
                    nodes[2].import_message_from_peer(nodes[1], msg1['message_id'])

                    for node in nodes:
                        node.commit()

                    (self + "2:Graph").update()

            class PostMessage(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node = graph.get_node(nodes[0])
                    text = (self + "2:Params-Text-Field").value.encode('utf-8')
                    msg = node.post_text_message(text)
                    node.commit()
                    (self + "2:Graph").update()

            class PostLink(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node = graph.get_node(nodes[0])
                    text = (self + "2:Params-Text-Field").value.encode('utf-8')
                    messages = [graph.get_message(message_id)
                                for message_id in (self + "2:Params-Messages-Field").value.strip().split(' ')]
                    msg = node.post_link_message(text, *messages)
                    node.commit()
                    (self + "2:Graph").update()

            class Subscribe(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    messages = (self + "2:Params-Messages-Field").value.strip().split(' ')
                    for message in messages:
                        node, message = graph.get_node_message(message)
                        node.update_local_subscription(message, subscribed = 1)
                        node.commit()
                    (self + "2:Graph").update()

            class Unsubscribe(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    messages = (self + "2:Params-Messages-Field").value.strip().split(' ')
                    for message in messages:
                        node, message = graph.get_node_message(message)
                        node.update_local_subscription(message, subscribed = 0)
                        node.commit()
                    (self + "2:Graph").update()

            class Erase(object):
                def clicked(self, path):
                    graph = self + "2:Graph"
                    messages = (self + "2:Params-Messages-Field").value.strip().split(' ')
                    for message in messages:
                        node, message = graph.get_node_message(message)
                        node.delete_local_subscription(message)
                        node.commit()
                    (self + "2:Graph").update()

        class Params(object):
            class Nodes(object):
                class Field(object):
                    pass
            class Messages(object):
                class Field(object):
                    pass
            class Subscriptions(object):
                class Field(object):
                    pass
            class Text(object):
                class Field(object):
                    pass

        class SubscriptionUpdates(object):
            class Child(object):
                def draw(self, output_options):
                    graph = self + "2:Graph"

                    res = {}
                    node_ids = (self + "2:Params-Nodes-Field").value.strip()
                    node_ids = node_ids and set(graph.s2id(node_id) for node_id in node_ids.split(' ')) or set()

                    for node_id in node_ids:
                        node = graph.get_node(graph.id2s(node_id))
                        res[node_id] = {}
                        for peer_id in node_ids:
                            with CliqueClique.Tables.SubscriptionUpdates.select_objs(
                                node._conn, node.node_id, peer_id) as subscriptions:
                                res[node_id][peer_id] = list(subscriptions)

                    return """
<table>
 <tr>
  <th>node</th>
  <th>peer</th>
  <th>message</th>
  <th>is subscribed</th>
  <th>center node is subscribed</th>
  <th>center distance</th>
  <th>send message</th>
  <th>delete subscription</th>
 </tr>
 %s
</table>
                        """ % ('\n'.join(
"""
<tr>
 <th colspan='3'>
  %s
 </th>
 <th colspan='5'></th>
</tr>
%s
""" % (CliqueClique.Visualizer.VisualizerOperations._id2label(node_id), '\n'.join(
"""
<tr>
 <th></th>
 <th colspan='2'>
  %s
 </th>
 <th colspan='5'></th>
</tr>
%s
""" % (CliqueClique.Visualizer.VisualizerOperations._id2label(peer_id), '\n'.join(
"""
<tr>
 <td></td>
 <td></td>
 <td>%(message_id)s</td>
 <td>%(is_subscribed)s</td>
 <td>%(center_node_is_subscribed)s</td>
 <td>%(center_distance)s</td>
 <td>%(send_message)s</td>
 <td>%(delete_subscription)s</td>
""" % CliqueClique.Visualizer.VisualizerOperations._ids2labels(dict(subscription_data))
                        for subscription_data in peer_data))
                        for (peer_id, peer_data) in node_data.iteritems()))
                        for (node_id, node_data) in res.iteritems()),)


        class Subscriptions(object):
            class Child(object):
                def draw(self, output_options):
                    graph = self + "2:Graph"
                    host = (self + "2:").host

                    res = {}
                    node_ids = (self + "2:Params-Nodes-Field").value.strip()
                    node_ids = node_ids and set(graph.s2id(node_id) for node_id in node_ids.split(' ')) or set()

                    with CliqueClique.Tables.UpstreamSubscription.select_objs(
                        host._conn, node_ids) as upstreams:
                        for upstream in upstreams:
                            add_to_tree(res, [upstream['node_id'], upstream['message_id'], 'up', upstream['peer_id']], upstream)

                    with CliqueClique.Tables.DownstreamSubscription.select_objs(
                        host._conn, node_ids) as downstreams:
                        for downstream in downstreams:
                            add_to_tree(res, [downstream['node_id'], downstream['message_id'], 'down', downstream['peer_id']], downstream)

                    return """
<table>
 <tr>
  <th>node</th>
  <th>message</th>
  <th>direction</th>
  <th>peer</th>
  <th>local is subscribed</th>
  <th>local center node is subscribed</th>
  <th>local center node id</th>
  <th>local center distance</th>
  <th>remote is subscribed</th>
  <th>remote center node is subscribed</th>
  <th>remote center node id</th>
  <th>remote center distance</th>
 </tr>
 %s
</table>
                        """ % ('\n'.join(
"""
<tr>
 <th colspan='4'>
  %s
 </th>
 <th colspan='8'></th>
</tr>
%s
""" % (CliqueClique.Visualizer.VisualizerOperations._id2label(node_id), '\n'.join(
"""
<tr>
 <th></th>
 <th colspan='3'>
  %s
 </th>
 <th colspan='8'></th>
</tr>
%s
""" % (CliqueClique.Visualizer.VisualizerOperations._id2label(message_id), '\n'.join(
"""
<tr>
 <th></th>
 <th></th>
 <th colspan='2'>
  %s
 </th>
 <th colspan='8'></th>
</tr>
%s
""" % (direction, '\n'.join(
"""
<tr>
 <td></td>
 <td></td>
 <td></td>
 <td>%(peer_id)s</td>
 <td>%(local_is_subscribed)s</td>
 <td>%(local_center_node_is_subscribed)s</td>
 <td>%(local_center_node_id)s</td>
 <td>%(local_center_distance)s</td>
 <td>%(remote_is_subscribed)s</td>
 <td>%(remote_center_node_is_subscribed)s</td>
 <td>%(remote_center_node_id)s</td>
 <td>%(remote_center_distance)s</td>
""" % CliqueClique.Visualizer.VisualizerOperations._ids2labels(dict(subscription_data))
                        for (peer_id, subscription_data) in direction_data.iteritems()))
                        for (direction, direction_data) in message_data.iteritems()))
                        for (message_id, message_data) in node_data.iteritems()))
                        for (node_id, node_data) in res.iteritems()),)

                
