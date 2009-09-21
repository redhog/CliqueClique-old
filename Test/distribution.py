# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# CliqueClique
# Copyright (C) 2009 Egil Moeller <redhog@redhog.org>

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

import CliqueClique.Host, CliqueClique.Node, md5, unittest

class TestDistribution(unittest.TestCase):
    @classmethod
    def node_num_to_id(cls, node_num):
        return md5.md5("node_%s" % node_num).hexdigest()

    def test_distribution_syncall(self):
        h = CliqueClique.Host.Host()
        h.initialize()
        nodes = [h.get_node(CliqueClique.Node.NodeOperations.s2id(self.node_num_to_id(x)),
                            last_seen_address="tcp:localhost:471%s" % x)
                 for x in xrange(0, 3)]

        msg1 = nodes[0].post_text_message('Message')
        msg2 = nodes[0].post_text_message('Comment')
        msglnk1 = nodes[0].post_link_message('Link', msg1, msg2)

        nodes[1].import_message_from_peer(nodes[0], msg1['message_id'])
        nodes[2].import_message_from_peer(nodes[1], msg1['message_id'])

        while nodes[0].sync_peers_locally(nodes[1]): pass
        
        self.assertEqual(nodes[1].get_message_by_expr(["content", "Link"]), None)

        nodes[1].update_local_subscription(msg1, subscribed = 1)

        while nodes[0].sync_peers_locally(nodes[1]): pass
        
        self.assertEqual(nodes[1].get_message_by_expr(["content", "Link"])["content"], "Link")
        self.assertEqual(nodes[1].get_message_by_expr(["content", "Comment"]), None)
