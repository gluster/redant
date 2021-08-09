"""
 Copyright (C) 2018  Red Hat, Inc. <http://www.redhat.com>

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
    Test peer probe while snapd is running.
"""

# disruptive;dist,rep
from tests.d_parent_test import DParentTest


class TestPeerProbeWhileSnapdRunning(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Create and start the volume
        """
        # Check server requirements
        redant.check_hardware_requirements(self.server_list, 4)

        # Detach on node
        self.extra_node = self.server_list[-1]
        self.redant.peer_detach(self.extra_node, self.server_list[0])

        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list[0:3],
                                 self.brick_roots, force=True)

    def run_test(self, redant):
        '''
        -> Create Volume
        -> Create snap for that volume
        -> Enable uss
        -> Check snapd running or not
        -> Probe a new node while snapd is running
        '''
        # creating Snap
        redant.snap_create(self.vol_name, 'snap1', self.server_list[0])

        # Enabling Snapd(USS)
        redant.enable_uss(self.vol_name, self.server_list[0])

        # Checking snapd running or not
        if not redant.is_snapd_running(self.vol_name, self.server_list[0]):
            raise Exception("Unexpected: Snapd is not running")

        # Probing new node
        if not redant.peer_probe_servers(self.extra_node,
                                         self.server_list[0]):
            raise Exception(f"Failed to peer probe node {self.extra_node}")
