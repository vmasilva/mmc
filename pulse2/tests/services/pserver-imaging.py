# -*- coding: utf-8; -*-
#
# (c) 2007-2010 Mandriva, http://www.mandriva.com/
#
# $Id$
#
# This file is part of Pulse 2, http://pulse2.mandriva.org
#
# Pulse 2 is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pulse 2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pulse 2.  If not, see <http://www.gnu.org/licenses/>.

"""
Unit tests for the imaging API of the Pulse 2 Package Server
"""

import os
import unittest
import xmlrpclib
from time import gmtime

from pulse2.utils import reduceMACAddress

from testutils import ipconfig

ipserver = ipconfig()
protocol = 'https' # protocol's server
server = xmlrpclib.ServerProxy('%s://%s:9990/imaging_api' % (protocol,ipserver))
mmcagent = xmlrpclib.ServerProxy('%s://mmc:s3cr3t@%s:7080' % (protocol, '127.0.0.1'))

menus = {}
menu = { 'timeout' : 20,
         'background_uri' : u'/##PULSE2_F_DISKLESS##/##PULSE2_F_BOOTSPLASH##',
         'name' : u'Default Boot Menu',
         'message' : u'-- Warning! Your PC is being backed up or restored. Do not reboot !',
         'protocol' : u'nfs',
         'default_item' : 1,
         'default_item_WOL' : 1,
         'bootservices' : { '1': { 'name' : u'Continue Normal Startup',
                                 'desc' : u'Start as usual',
                                 'value' : u'root (hd0)\nchainloader +1',
                                 'hidden' : 0,
                                 'hidden_WOL' : 0,
                                 'value' : u'root (hd0)\nchainloader +1' },
                           '2': { 'name' : u'Register a Pulse 2 Client',
                                'desc' : u'Record this computer in Pulse 2 Server',
                                'value' : u'identify L=##PULSE2_LANG## P=none\nreboot' }
                            },
         'images' : { '5' : { 'uuid': u'302c19d2-212b-4b9a-b04e-4fced0b83466',
                            'name' : u'Image computer.example.net',
                            'desc' : u'(Thu Dec  3 15:20:02 2009)',
                            'post_install_script_dis' : { 'id' : 2,
                                                      'name' : u'...',
                                                      'desc' : u'...',
                                                      'value' : '...'
                                                    }
                            }
                    },
         'target' : { 'name' : u'...',
                      'kernel_parameters' : u'...',
                      'image_parameters' : u'....',
                    }
        }
menus = { 'UUID27' : menu }

class Imaging(unittest.TestCase):

    def test_01registerPackageServer(self):
        ret = os.system('pulse2-package-server-register-imaging  -n \"Pulse 2 imaging\" -m http://mmc:s3cr3t@localhost:7080')
        self.assertEqual(0, ret)
        self.assertEqual([True], mmcagent.imaging.linkImagingServerToLocation('UUID1', 'UUID1', 'root'))

    def test_02registerComputer(self):
        mac = '00:11:22:33:44:ff'
        result = server.computerRegister('foobar', 'BADMAC')
        self.assertFalse(result)
        result = server.computerRegister('bad _ name', mac)
        self.assertFalse(result)
        result = server.computerRegister('foobar', mac)
        self.assertTrue(result)
        self.assertTrue(os.path.exists('/var/lib/pulse2/imaging/uuid-cache.txt'))
        self.assertTrue(os.path.isdir('/var/lib/pulse2/imaging/computers/%s' % 'UUID1'))
        self.assertTrue(os.path.exists('/var/lib/pulse2/imaging/bootmenus/%s' % reduceMACAddress(mac)))

    def atest_computersMenuSet(self):
        #result = server.computersMenuSet([('UUID17', {})])
        #self.assertEqual(['UUID1'], result)
        result = server.computersMenuSet(menus)
        self.assertEqual(['UUID27'], result)

    def atest_logClientAction(self):
        result = server.logClientAction('mac', 'level', 'phase', 'message')
        self.assertTrue('faultCode' in result and
                        'TypeError' in result['faultCode'])
        result = server.logClientAction('00:11:22:33:44:55', 'level', 'phase', 'message')
        self.assertTrue(result)

    def atest_computerUpdate(self):
        result = server.computerUpdate('BADMAC')
        self.assertTrue('faultCode' in result and
                        'TypeError' in result['faultCode'])        
        
    def atest_status(self):
        result = server.imagingServerStatus()
        self.assertEqual(dict, type(result))
        self.assertTrue('space_available' in result)
        self.assertTrue('mem_info' in result)
        self.assertTrue('uptime' in result)
        self.assertTrue('stats' in result)

    def atest_injectInventory(self):
        pass

    def atest_02getComputerByMAC(self):
        result = server.getComputerByMac('BADMAC')
        self.assertTrue('faultCode' in result and
                        'TypeError' in result['faultCode'])
        result = server.getComputerByMac('00:11:22:33:44:55')
        self.assertTrue('uuid' in result and result['uuid'] == 'FAKE_UUID')

    def atest_imagingServerImageDelete(self):
        result = server.imagingServerImageDelete('foo')
        self.assertFalse(result)
        result = server.imagingServerImageDelete('35f23420-4050-4734-b172-d458915ef17d')
        self.assertFalse(result)

    def atest_imageRegister(self):
        result = server.imageRegister('30:11:22:33:44:ff', '35f23420-4050-4734-b172-d458915ef17d', False, 'Image 1', 'Mon Mar  1 15:46:43 CET 2010', '/path/?', 12345, tuple(gmtime()), 'cdelfosse')
        self.assertTrue(result)

    def atest_imagingServerDefaultMenuSet(self):
        result = server.imagingServerDefaultMenuSet(menu)
        self.assertEqual(['UUID1'], result)
        

if __name__ == '__main__':
    unittest.main()