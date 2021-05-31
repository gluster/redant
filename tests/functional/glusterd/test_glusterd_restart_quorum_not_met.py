
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
    Test brick status when quorum isn't met after glusterd restart.
"""

from tests.d_parent_test import DParentTest

# disruptive;dist,dist-rep,dist-arb,dist-disp,rep,disp,arb


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test Brick status when Quorum is not met after glusterd restart.
        1. Create a volume and mount it.
        2. Set the quorum type to 'server'.
        3. Bring some nodes down such that quorum won't be met.
        4. Brick status should be offline in the node which is up.
        5. Restart glusterd in this node.
        6. The brick status still should be offline as quorum isn't met.
        """
        # Set the quorum type to server and validate it.
        vol_option = {'cluster.server-quorum-type': 'server'}
        redant.set_volume_options(self.vol_name,
                                  vol_option,
                                  self.server_list[0])
        # Get the brick list.
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])

        # Stop glusterd processes.
        for server in self.server_list[1:]:
            redant.stop_glusterd(server)

        # Get the brick status in a node where glusterd is up.
        ret = redant.are_bricks_offline(self.vol_name, brick_list[0:1],
                                        self.server_list[0])
        if not ret:
            raise Exception("Bricks are online")

        # Restart one of the node which is up.
        redant.restart_glusterd(self.server_list[0])

        # Wait for glusterd to be online and validate it's running.
        ret = redant.wait_for_glusterd_to_start(self.server_list[0])
        if not ret:
            raise Exception(f"Glusterd not running on {self.server_list[0]}")

        # Get the brick status from the restarted node.
        ret = redant.are_bricks_offline(self.vol_name, brick_list[0:1],
                                        self.server_list[0])
        if not ret:
            raise Exception("Bricks are online")

        # Start glusterd on all servers.
        for server in self.server_list:
            redant.start_glusterd(server)

        # Wait for glusterd to start.
        for server in self.server_list:
            ret = redant.wait_for_glusterd_to_start(server)
            if not ret:
                raise Exception(f"Glusterd not started on {server}")

        # Wait for all volume processes to be online
        ret = redant.wait_for_volume_process_to_be_online(self.vol_name,
                                                          self.server_list[0],
                                                          self.server_list,
                                                          timeout=600)
        if not ret:
            raise Exception("Not all volume processes are online")
