#
# (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
#
# $Id: __init__.py 3 2008-03-03 14:35:11Z cdelfosse $
#
# This file is part of MMC.
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

from mmc.support.config import PluginConfig
from mmc.support.mmctools import Singleton, xmlrpcCleanup
from mmc.plugins.inventory.utilities import getInventoryParts

from ConfigParser import NoOptionError
import logging

class InventoryExpertModeConfig(PluginConfig):

    def readConf(self):
        PluginConfig.readConf(self)
        self.expert_mode = {}
        self.graph = {}
        for i in getInventoryParts():
            try:
                self.graph[i] = self.get("graph", i).split('|')
            except NoOptionError:
                self.graph[i] = []
            try:
                self.expert_mode[i] = self.get("expert_mode", i).split('|')
            except NoOptionError:
                self.expert_mode[i] = []

class InventoryConfig(PluginConfig):

    def readConf(self):
        PluginConfig.readConf(self)
        self.dbdriver = self.get("main", "dbdriver")
        self.dbhost = self.get("main", "dbhost")
        self.dbname = self.get("main", "dbname")
        self.dbuser = self.get("main", "dbuser")
        self.dbpasswd = self.get("main", "dbpasswd")
        self.disable = (str(self.get("main", "disable")) == '1')
        try:
            self.dbpoolrecycle = self.getint("main", "dbpoolrecycle")
        except NoOptionError:
            self.dbpoolrecycle = None
                                                                        
        try:
            self.dbport = self.getint("main", "dbport")
        except NoOptionError:
            # We will use the default db driver port
            self.dbport = None


