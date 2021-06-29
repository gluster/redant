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

Description: Test case to check if the rebalance hangs after a node
is stopped.
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway, then node might need to be started,
        IO to be completed and then parent terminate to be invoked.
        """
        try:
            self.redant.start_glusterd(self.server_list[1])
            if not self.redant.wait_for_glusterd_to_start(self.server_list[1]):
                raise Exception("Failed to start glusterd on node "
                                f" {self.server_list[1]}")
            self.redant.cleanup_volume(self.vol_name, self.server_list[0])
            if self.list_of_procs != []:
                if not self.redant.wait_for_io_to_complete(self.list_of_procs,
                                                           self.mnt_list):
                    raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        In this test case:
        1. Trusted storage Pool of 2 nodes
        2. Create a distributed volumes with 2 bricks
        3. Start the volume
        4. Mount the volume
        5. Add some data file on mount
        6. Start rebalance with force
        7. kill glusterd on 2nd node
        8. Issue volume related command
        """
        self.list_of_procs = []

        redant.create_cluster(self.server_list[:2])
        redant.wait_till_all_peers_connected(self.server_list[:2])

        self.vol_type_inf['dist']['dist-count'] = 2
        vol_params_dict = self.vol_type_inf['dist']
        redant.volume_create(self.vol_name, self.server_list[0],
                             vol_params_dict, self.server_list[:2],
                             self.brick_roots, True)

        redant.volume_start(self.vol_name, self.server_list[0], True)
        if not redant.wait_for_vol_to_come_online(self.vol_name,
                                                  self.server_list[0]):
            raise Exception(f"Volume start for {self.vol_name} failed.")

        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

        self.list_of_procs = []
        proc = redant.create_deep_dirs_with_files(self.mountpoint, 1, 2, 3, 3,
                                                  5, self.client_list[0])
        self.list_of_procs.append(proc)

        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        if not redant.validate_io_procs(self.list_of_procs, self.mnt_list):
            raise Exception("IO Validation failed")
        self.list_of_procs = []

        redant.rebalance_start(self.vol_name, self.server_list[0], False,
                               True)

        redant.stop_glusterd(self.server_list[1])
        if not redant.wait_for_glusterd_to_stop(self.server_list[1]):
            raise Exception("Failed to stop glusterd on "
                            f"{self.server_list[1]}.")

        if not redant.wait_for_rebalance_to_complete(self.vol_name,
                                                     self.server_list[0]):
            raise Exception(f"Rebalance not yet complete for {self.vol_name}"
                            f" on {self.server_list[0]}")

        if redant.get_volume_status(self.vol_name,
                                    self.server_list[0]) is None:
            raise Exception(f"Failed to get volume status for {self.vol_name}")

        redant.start_glusterd(self.server_list[1])
        if not redant.wait_for_glusterd_to_start(self.server_list[1]):
            raise Exception("Failed to start glusterd on node "
                            f" {self.server_list[1]}")
