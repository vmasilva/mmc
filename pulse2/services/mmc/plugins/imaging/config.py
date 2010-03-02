# -*- coding: utf-8; -*-
#
# (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
# (c) 2007 Mandriva, http://www.mandriva.com/
#
# $Id$
#
# This file is part of Mandriva Management Console (MMC).
#
# MMC is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MMC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MMC; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
Configuration reader for imaging
"""

from mmc.support import mmctools
from mmc.support.config import PluginConfig
from pulse2.database.imaging.config import ImagingDatabaseConfig

class ImagingConfig(ImagingDatabaseConfig):
    disable = True
    web_def_date_fmt = "%Y-%m-%d %H:%M:%S"
    web_def_default_protocol = 'nfs'
    web_def_default_menu_name = 'Menu'
    web_def_default_timeout = '60'
    web_def_default_background_uri = ''
    web_def_default_message = 'Warning ! Your PC is being backed up or restored. Do not reboot !'

    def init(self, name = 'imaging', conffile = None):
        self.dbsection = "database"
        self.name = name
        if not conffile: self.conffile = mmctools.getConfigFile(name)
        else: self.conffile = conffile

        ImagingDatabaseConfig.setup(self, self.conffile)
        self.setup(self.conffile)

    def setup(self, conf_file):
        """
        Read the module configuration

        Currently used params:
        - section "imaging":
          + revopath
          + publicdir
        """
        self.disable = self.cp.getboolean("main", "disable")

        if self.cp.has_section("web"):
            for i in ('date_fmt', 'default_protocol', 'default_menu_name', 'default_timeout', 'default_background_uri', 'default_message'):
                full_name = "web_def_%s"%(i)
                if self.cp.has_option("web", full_name):
                    setattr(self, full_name, self.cp.get("web", full_name))

    def setDefault(self):
        """
        Set default values
        """
        PluginConfig.setDefault(self)
