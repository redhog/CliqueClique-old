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

import pydot
import Webwidgets
import sqlite3
import md5
import CliqueClique.Host, CliqueClique.Visualizer, CliqueClique.Tables

def node_num_to_id(node_num):
    return md5.md5("node_%s" % node_num).hexdigest()

class MainWindow(object):
    class Body(object):
        def __init__(self, *arg, **kw):
            Webwidgets.Html.__init__(self, *arg, **kw)
            self.host = CliqueClique.Host.Host()
            
        class Graph(CliqueClique.Visualizer.Visualizer):
            def __init__(self, *arg, **kw):
                Webwidgets.DotGraph.__init__(self, *arg, **kw)
                CliqueClique.Visualizer.Visualizer.__init__(self)
                
            def update(self):
                self.clear()
                self.add_host(self.parent.host)

            def add_node(self, node, **kw):
                if node.node_id in (self + "1:Params-Nodes-Field").value: 
                    kw['style'] = 'filled'
                    kw['fillcolor'] = self.node_color
                CliqueClique.Visualizer.Visualizer.add_node(
                    self, node, URL = self.calculate_callback_url('node:%s' % (node.node_id,)), **kw)

            def add_message(self, node, message, local_subscription, **kw):
                id_name = '%s:%s' % (node.node_id,
                                     message['message_id'])
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
                id_name = '%s:%s:%s' % (node.node_id,
                                        subscription['message_id'],
                                        subscription['peer_id'])
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
                    host = (self + "2:").host
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    for node in nodes:
                        node = host.get_node(node, True)
                        node.sync_self()
                        node.commit()
                    (self + "2:Graph").update()
            class Sync(object):
                def clicked(self, path):
                    host = (self + "2:").host
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node1 = host.get_node(nodes[0], True)
                    node2 = host.get_node(nodes[1], True)
                    node1.sync_peer(node2)
                    node1.commit()
                    node2.commit()
                    (self + "2:Graph").update()
            class RevSync(object):
                def clicked(self, path):
                    host = (self + "2:").host
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node1 = host.get_node(nodes[0], True)
                    node2 = host.get_node(nodes[1], True)
                    node2.sync_peer(node1)
                    node1.commit()
                    node2.commit()
                    (self + "2:Graph").update()
            class SyncBoth(object):
                def clicked(self, path):
                    host = (self + "2:").host
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node1 = host.get_node(nodes[0], True)
                    node2 = host.get_node(nodes[1], True)
                    node2.sync_peers(node1)
                    node1.commit()
                    node2.commit()
                    (self + "2:Graph").update()
            class SyncAll(object):
                def clicked(self, path):
                    host = (self + "2:").host
                    nodes = (self + "2:Params-Nodes-Field").value.strip().split(' ')
                    node1 = host.get_node(nodes[0], True)
                    node2 = host.get_node(nodes[1], True)
                    while node2.sync_peers_locally(node1): pass
                    node1.commit()
                    node2.commit()
                    (self + "2:Graph").update()

            class Initialize(object):
                pass

            class CreateTestData(object):
                def clicked(self, path):
                    host = (self + "2:").host
                    host.initialize()
                    poster_node = host.get_node(node_num_to_id(0), True)
                    msg1 = poster_node.post_text_message('Message')
                    msg2 = poster_node.post_text_message('Comment')
                    msglnk1 = poster_node.post_link_message('Link', msg1, msg2)
                    other_node = host.get_node(node_num_to_id(1), True)
                    other_node.import_message_from_peer(poster_node, msg1['message_id'])
                    poster_node.commit()
                    other_node.commit()
                    (self + "2:Graph").update()

            class PostMessage(object):
                def clicked(self, path):
                    pass

            class PostLink(object):
                def clicked(self, path):
                    pass

            class Subscribe(object):
                def clicked(self, path):
                    host = (self + "2:").host
                    messages = (self + "2:Params-Messages-Field").value.strip().split(' ')
                    for message in messages:
                        node_id, message_id = message.split(':')
                        node = host.get_node(node_id, True)
                        node.update_local_subscription(node.get_message(message_id), subscribed = 1)
                        node.commit()
                    (self + "2:Graph").update()

            class Unsubscribe(object):
                def clicked(self, path):
                    host = (self + "2:").host
                    messages = (self + "2:Params-Messages-Field").value.strip().split(' ')
                    for message in messages:
                        node_id, message_id = message.split(':')
                        node = host.get_node(node_id, True)
                        node.update_local_subscription(node.get_message(message_id), subscribed = 0)
                        node.commit()
                    (self + "2:Graph").update()

            class Erase(object):
                def clicked(self, path):
                    host = (self + "2:").host
                    messages = (self + "2:Params-Messages-Field").value.strip().split(' ')
                    for message in messages:
                        node_id, message_id = message.split(':')
                        node = host.get_node(node_id, True)
                        node.delete_local_subscription(node.get_message(message_id))
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
            def draw(self, output_options):
                host = (self + "1:").host

                res = {}
                node_ids = (self + "1:Params-Nodes-Field").value.strip()
                node_ids = node_ids and set(node_ids.split(' ')) or []

                for node_id in node_ids:
                    node = host.get_node(node_id, True)
                    res[node_id] = {}
                    for peer_id in node_ids:
                        res[node_id][peer_id] = CliqueClique.Tables.SubscriptionUpdates.select_objs(
                            node.conn, node.node_id, peer_id)

                return """
<table>
 <tr>
  <th>node</th>
  <th>peer</th>
  <th>message</th>
  <th>is_subscribed</th>
  <th>center_distance</th>
  <th>send_message</th>
  <th>delete_subscription</th>
 </tr>
 %s
</table>
                        """ % ('\n'.join(
"""
<tr>
 <th colspan='3'>
  %s
 </th>
 <th colspan='4'></th>
</tr>
%s
""" % (node_id, '\n'.join(
"""
<tr>
 <th></th>
 <th colspan='2'>
  %s
 </th>
 <th colspan='4'></th>
</tr>
%s
""" % (peer_id, '\n'.join(
"""
<tr>
 <td></td>
 <td></td>
 <td>%(message_id)s</td>
 <td>%(is_subscribed)s</td>
 <td>%(center_distance)s</td>
 <td>%(send_message)s</td>
 <td>%(delete_subscription)s</td>
""" % subscription_data
                        for subscription_data in peer_data))
                        for (peer_id, peer_data) in node_data.iteritems()))
                        for (node_id, node_data) in res.iteritems()),)
