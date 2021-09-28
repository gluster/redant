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

 You should have received a copy of the GNU General Public License along`
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    TC to check remove-brick operation when a brick process is killed
"""

# disruptive;dist-rep,dist-arb
from copy import deepcopy
from random import choice
from tests.d_parent_test import DParentTest


class TestKillBrickWithRemoveBrick(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 3

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create some data on the volume.
        3. Start remove-brick on the volume.
        4. When remove-brick is in progress kill brick process of a brick
           which is being remove.
        5. Remove-brick should complete without any failures.
        """
        # Start I/O from clients on the volume
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        counter = 1
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      counter, 2, 8, 5, 5,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            counter += 10

        # Complete IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("Failed to complete IO")

        # Collect arequal checksum before ops
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts)

        # Start remove-brick on the volume
        brick_list = (redant.form_bricks_list_to_remove_brick(
                      self.server_list[0], self.vol_name))

        if brick_list is None:
            raise Exception("Failed to form bricks list to remove-brick. "
                            f"Hence unable to shrink volume {self.vol_name}")

        # Shrink volume
        redant.remove_brick(self.server_list[0], self.vol_name,
                            brick_list, "start")

        # Check rebalance is in progress
        ret = redant.get_remove_brick_status(self.server_list[0],
                                             self.vol_name, brick_list)
        if not ret:
            raise Exception("Failed ot get remove brick status")

        if ret['aggregate']['statusStr'] != "in progress":
            raise Exception("Rebalance is not in 'in progress' state, either "
                            "rebalance is in completed state or failed to "
                            "get rebalance status")

        # kill brick process of a brick which is being removed
        brick = choice(brick_list)
        node, _ = brick.split(":")
        ret = redant.kill_process(node, process_names="glusterfsd")
        if not ret:
            raise Exception(f"Failed to kill brick process of brick {brick}")

        # Wait for remove-brick to complete on the volume
        ret = redant.wait_for_remove_brick_to_complete(self.server_list[0],
                                                       self.vol_name,
                                                       brick_list)
        if not ret:
            raise Exception("Remove-brick didn't complete")

        # Check for data loss by comparing arequal before and after ops
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts)
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum is NOT MATCHNG")
