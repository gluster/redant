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

Description: Test to verify the brick status under quorum.
"""

from tests.d_parent_test import DParentTest

# disruptive;dist-rep


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. Create volume
        2. Enable server quorum on volume
        3. Stop glusterd on all nodes except first node
        4. Verify brick status of nodes where glusterd is running with
        default quorum ratio(51%)
        5. Change the cluster.server-quorum-ratio from default to 95%
        6. Start glusterd on all servers except last node
        7. Verify the brick status again
        """

        redant.set_volume_options(self.vol_name,
                                  {'cluster.server-quorum-type': 'server'},
                                  self.server_list[0])

        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception(f"Brick list for {self.vol_name} is None")

        redant.stop_glusterd(self.server_list[1:])
        if not redant.wait_for_glusterd_to_stop(self.server_list[1:]):
            raise Exception(f"Glusterd not stopped in {self.server_list[1:]}")

        if not redant.are_bricks_offline(self.vol_name, brick_list,
                                         self.server_list[0]):
            raise Exception("Bricks are expected to be offline but aren't.")

        redant.set_volume_options('all',
                                  {'cluster.server-quorum-ratio': '95%'},
                                  self.server_list[0])

        redant.start_glusterd(self.server_list[1:])
        if not redant.wait_for_glusterd_to_start(self.server_list[1:]):
            raise Exception(f"Glusterd not started in {self.server_list[1:]}")

        if not redant.wait_for_bricks_to_come_online(self.vol_name,
                                                     self.server_list,
                                                     brick_list):
            raise Exception("Bricks are not yet online.")
