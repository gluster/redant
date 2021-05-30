"""
Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>

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
"""

import random
from tests.d_parent_test import DParentTest

# disruptive;dist,disp,dist-disp


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. Enabling serve quorum
        2. start the volume
        3. Set server quorum ratio to 95%
        4. Stop the glusterd of any one of the node
        5. Perform rebalance operation operation
        6. Check gluster volume status
        7. start glusterd
        """
        redant.volume_stop(self.vol_name, self.server_list[0], True)
        if not redant.wait_for_vol_to_go_offline(self.vol_name,
                                                 self.server_list[0]):
            raise Exception(f"Failed to stop volume {self.vol_name} in node"
                            f" {self.server_list[0]}")

        redant.set_volume_options(self.vol_name,
                                  {'cluster.server-quorum-type': 'server'},
                                  self.server_list[0])

        redant.volume_start(self.vol_name, self.server_list[0])
        if not redant.wait_for_vol_to_come_online(self.vol_name,
                                                  self.server_list[0]):
            raise Exception(f"Failed to start the volume {self.vol_name} in "
                            f" node {self.server_list[0]}")

        redant.set_volume_options('all',
                                  {'cluster.server-quorum-ratio': '95%'},
                                  self.server_list[0])

        self.random_server = random.choice(self.server_list[1:])
        redant.stop_glusterd(self.random_server)
        if not redant.wait_for_glusterd_to_stop(self.random_server):
            raise Exception("Failed to stop glusterd on node "
                            f" {self.random_server}")

        msg = (f"volume rebalance: {self.vol_name}: failed: Quorum not met."
               " Volume operation not allowed.")
        ret = redant.rebalance_start(self.vol_name, self.server_list[0],
                                     excep=False)
        if msg != ret['error_msg'][:-1]:
            raise Exception("Rebalance shouldn't have started for volume"
                            f" {self.vol_name}")

        ret = redant.get_volume_status(self.vol_name, self.server_list[0])
        if ret[self.vol_name]['tasks'] is not None:
            raise Exception("Rebalance has started!")

        redant.start_glusterd(self.random_server)
        if not redant.wait_for_glusterd_to_start(self.random_server):
            raise Exception("Failed to start glusterd on node"
                            f" {self.random_server}")
