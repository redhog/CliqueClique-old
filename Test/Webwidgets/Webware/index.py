#! /bin/env python
# -*- coding: UTF-8 -*-
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


import Webwidgets

Webwidgets.Program.Session.debug_fields = False
Webwidgets.Program.Session.debug_field_input = False
Webwidgets.Program.Session.debug_receive_notification = False
Webwidgets.Program.Session.debug_arguments = False
Webwidgets.Program.debug = True
Webwidgets.Widgets.Base.debug_exceptions = True
Webwidgets.Widgets.Base.log_exceptions = True
Webwidgets.Wwml.debug_import = True

import CliqueClique.Test.Webwidgets.UI

class index(Webwidgets.Program):
    class Session(Webwidgets.Program.Session):
        def new_window(self, win_id):
            return CliqueClique.Test.Webwidgets.UI.MainWindow(self, win_id)
