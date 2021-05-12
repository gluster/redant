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
      Test quorum cli commands in glusterd
"""

# disruptive;rep,dist,disp,arb,dist-arb,dist-rep

from tests.d_parent_test import DParenttTest


class TestCase(DParentTest):

    def _set_and_validate_quorum_option(self, options_dict: dict,
                                        vol: str = 'all'):
        """
        Method to handle the repetitive calls for setting quorum
        options such as quorum ratio and quorum type.
        """
        self.redant.set_volume_options(vol, options_dict, self.server_list[0])
        self.redant.validate_volume_option(vol, options_dict,
                                           self.server_list[0])

    def run_test(self, redant):
        """
        Test quorum CLI commands on glusterd
        1. Create a volume and start it.
        2. Set the quorum type to 'server' and verify it.
        3. Set the quorum type to 'none' and verify it.
        4. Set the quorum ratio and verify it.
        """
        # Set server quorum type to 'server' and validate it
        self._set_and_validate_quorum_option({'cluster.server-quorum-type':
                                              'server'}, self.vol_name)

        # Set server quorum type to 'none' and validate it
        self._set_and_validate_quorum_option({'cluster.server-quorum-type':
                                              'none'}, self.vol_name)

        # Set server quorum ratio to 90% and validate it
        self._set_and_validate_quorum_option({'cluster.server-quorum-ratio':
                                              '90%'})

        # Resetting all volume options.
        redant.reset_volume_option(self.vol_name, "all", self.server_list[0])
