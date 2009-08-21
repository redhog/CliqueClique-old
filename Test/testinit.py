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
import md5, threading
import CliqueClique.Host, CliqueClique.Node, CliqueClique.Visualizer, CliqueClique.Tables

host = CliqueClique.Host.Host()

class Th(threading.Thread):
    def run(self):
        print "Begin: %s" % (self.getName())
        host.initialize()

        poster_node = host.get_node(CliqueClique.Node.NodeOperations.s2id( md5.md5("node_1").hexdigest()))
        
        print "Done: %s" % (self.getName())

for x in (1, 2):
    th = Th(name="Th %s" % x)
    th.start()
    th.join()
