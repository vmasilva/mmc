# (c) 2011 Mandriva, http://www.mandriva.com
#
# $Id$
#
# This file is part of Mandriva Pulse2 project.
#
# This software is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s):
#   Jean Parpaillon <jparpaillon@mandriva.com>
#
pulseconfdir = $(sysconfdir)/mmc/pulse2

certpaths = \
	package-server/keys inventory-server/keys scheduler/keys \
	launchers/keys
certca = $(patsubst %,%/cacert.pem,$(certpaths))
certpriv = $(patsubst %,%/privkey.pem,$(certpaths))

nobase_pulseconf_DATA = \
	package-server/package-server.ini inventory-server/inventory-server.ini \
	scheduler/scheduler.ini launchers/launchers.ini atftpd/pcre.conf \
	$(certca) $(certpriv)

EXTRA_DIST = $(nobase_pulseconf_DATA)

if ENABLE_CONF_BACKUP
INSTALL += --backup=numbered
endif