"""
  Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

  Description:
    Test set and reset of storage reserve limit in glusterd
"""

# nonDisruptive;rep,dist,arb,disp,dist-rep,dist-arb,dist-disp

from tests.abstract_test import AbstractTest


class TestCase(AbstractTest):
    """ Testing set and reset of Reserve limit in GlusterD """

    def run_test(self, redant):
        """
        Test set and reset of reserve limit on glusterd
        1. Create a volume and start it.
        2. Set storage.reserve limit on the created volume and verify it.
        3. Reset storage.reserve limit on the created volume and verify it.
        """
        redant.set_volume_options(self.vol_name, {'storage.reserve': '50'},
                                  self.server_list[0])
        redant.validate_volume_option(self.vol_name,
                                      {'storage.reserve': '50'},
                                      self.server_list[0])
        redant.reset_volume_option(self.vol_name, 'storage.reserve',
                                   self.server_list[0])
        redant.validate_volume_option(self.vol_name,
                                      {'storage.reserve': '1 (DEFAULT)'},
                                      self.server_list[0])
