# (c) 2011 Mandriva, http://www.mandriva.com
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
# along with MMC.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s):
#   Jean Parpaillon <jparpaillon@mandriva.com>
#
clientsdir = $(localstatedir)/lib/pulse2/clients/win32

if ENABLE_NSIS
# Installer is generated with NSIS
installerversion = $(VERSION)
else
# Installer is the latest version available on website
installerversion = 1.3.1.1
endif
installer = pulse2-win32-agents-installer-$(installerversion).exe
installernsi = pulse2-win32-agents-installer.nsi
installerdata = \
	artwork/header.bmp \
	artwork/uninstall.ico \
	artwork/wizard.bmp \
	artwork/install.ico \
	libs/StrRep.nsh \
	libs/ServiceLib.nsh \
	inventoryoptions.ini

if ENABLE_NSIS
clients_SCRIPTS = $(installer)
endif
dist_clients_SCRIPTS = build.sh
clients_DATA = sfx.conf.in win32.mk 7zsd.sfx \
	remote-desktop-agent-vnc2.reg

dist_doc_DATA = README.win32

EXTRA_DIST = \
	build.sh \
	win32.mk.in \
	sfx.conf.in \
	7zsd.sfx \
	remote-desktop-agent-vnc2.reg \
	$(installernsi) \
	$(installerdata)

CLEANFILES = win32.mk $(installer)

$(installer): $(installernsi) $(installerdata)
	if test "$(builddir)" != "$(srcdir)"; then \
	  for dep in $(installerdata); do \
	    mkdir -p `dirname $$dep`; \
	    cp $(srcdir)/$$dep $$dep; \
	  done; \
	fi
	makensis $<
	if test "$(builddir)" != "$(srcdir)"; then \
	  for dep in $(installerdata); do \
	    rm -f $$dep; \
	  done; \
	fi

edit = sed \
	-e 's|@VERSION[@]|$(VERSION)|g' \
	-e 's|@installerversion[@]|$(installerversion)|g' \
        -e 's|@localstatedir[@]|$(localstatedir)|g'

win32.mk: Makefile
	rm -f $@ $@.tmp
	$(MKDIR_P) $(@D)
	srcdir=''; \
	  test -f ./$@.in || srcdir=$(srcdir)/; \
	  $(edit) $${srcdir}$@.in >$@.tmp
	mv $@.tmp $@

win32.mk: win32.mk.in
