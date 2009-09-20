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

class TestNametree(unittest.TestCase):
    @classmethod
    def node_num_to_id(cls, node_num):
        return md5.md5("node_%s" % node_num).hexdigest()

    def test_nametree(self):
        h = CliqueClique.Host.Host()
        n0 = h.get_node(CliqueClique.Node.NodeOperations.s2id(self.node_num_to_id(0)))

        for s in ('foobar', 'food', 'kafoo'):
            n0.post_direntrylink_message(
                n0.get_message_by_expr(["system", "rootdir"]),
                s,
                n0.post_text_message('entry:' + s))

        self.assertEqual(n0.get_message_by_expr(['nametreelookupentry', 'foobar', n0.get_message_by_expr(["system", "rootdir"])])['content'],
                         'entry:foobar')
