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

Description: This test case aims to verify the gluster get-state command.
"""


from tests.nd_parent_test import NdParentTest

# nonDisruptive;dist-disp,rep,arb,dist-rep,dist,disp,dist-arb


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. Stop the volume.
        2. Execute "gluster get-state" and verify that a brick is offline.
        3. Start the volume and verify that a brick is online.
        4. Kill a brick in a node and verify with get-state that it is
           offline.
        5. With get-state check that the brick in some other node is online.
        6. Get the offline brick online.
        """
        redant.volume_stop(self.vol_name, self.server_list[0], True)

        if not redant.wait_for_vol_to_go_offline(self.vol_name,
                                                 self.server_list[0]):
            raise Exception(f"Failed to stop volume {self.vol_name} on node"
                            f" {self.server_list[0]}")

        ret = redant.get_state(self.server_list[0])
        if ret['Volumes']['volume1.brick1.status'].strip() != "Stopped":
            raise Exception("Brick not in stopped mode after volume stop.")

        redant.volume_start(self.vol_name, self.server_list[0])
        if not redant.wait_for_vol_to_come_online(self.vol_name,
                                                  self.server_list[0]):
            raise Exception(f"Failed to start volume {self.vol_name} on node"
                            f" {self.server_list[0]}")

        ret = redant.get_state(self.server_list[0])
        if ret['Volumes']['volume1.brick1.status'].strip() != "Started":
            raise Exception("Brick not in started mode after volume start")

        vol_bricks = redant.get_online_bricks_list(self.vol_name,
                                                   self.server_list[0])
        if vol_bricks is None:
            raise Exception("Failed to get online brick list for the volume"
                            f" {self.vol_name} on node {self.server_list[0]}")

        if not redant.bring_bricks_offline(self.vol_name, vol_bricks[0]):
            raise Exception(f"Failed to bring brick {vol_bricks[0]} offline"
                            f" of volume {self.vol_name}")

        ret = redant.get_state(self.server_list[0])
        if ret['Volumes']['volume1.brick1.status'].strip() != "Stopped":
            raise Exception("Brick not in stopped mode after volume stop.")

        ret = redant.get_state(self.server_list[1])
        if ret['Volumes']['volume1.brick2.status'].strip() != "Started":
            raise Exception("Brick not in started mode after volume start")

        offline_brick = redant.get_offline_bricks_list(self.vol_name,
                                                       self.server_list[0])
        if offline_brick is None:
            raise Exception("Failed to get offline brick list for the volume"
                            f" {self.vol_name} on node {self.server_list[0]}")
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick):
            raise Exception(f"Failed to get offline bricks {offline_brick} to"
                            f" online state")
