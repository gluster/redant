"""
 Copyright (C) 2018 Red Hat, Inc. http://www.redhat.com>

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
    TC to induce holes by remove brick and then fix layout
"""

# disruptive;dist,dist-rep,dist-disp
from common.ops.gluster_ops.constants import (TEST_LAYOUT_IS_COMPLETE,
                                              FILETYPE_DIRS)
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestRebalanceValidation(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        if self.volume_type == "dist-rep":
            conf_hash['dist_count'] = 4
        elif self.volume_type == "dist-disp":
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
        Steps:
        - Create and start a volume
        - Mount the volume on client
        - Create a directory on mountpoint
        - Validate the layout is complete
        - Shrink the volume
        - Validate the layout is not complete
        - Start rebalance fix-layout
        - Wait for rebalance to complete
        - Validate layout is complete
        """
        redant.create_dir(self.mountpoint, "testdir", self.client_list[0])

        # DHT Layout validation
        ret = redant.validate_files_in_dir(self.client_list[0],
                                           self.mountpoint,
                                           test_type=TEST_LAYOUT_IS_COMPLETE,
                                           file_type=FILETYPE_DIRS)
        if not ret:
            raise Exception("LAYOUT_IS_COMPLETE: FAILED")

        # Log Volume Info and Status before shrinking the volume.
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Shrinking volume by removing bricks
        bricks_list_to_remove = (redant.form_bricks_list_to_remove_brick(
                                 self.server_list[0], self.vol_name,
                                 subvol_num=1))

        if bricks_list_to_remove is None:
            raise Exception("Failed to form bricks list to remove-brick. "
                            f"Hence unable to shrink volume {self.vol_name}")

        redant.remove_brick(self.server_list[0], self.vol_name,
                            bricks_list_to_remove, "force")

        # Check the layout
        ret = redant.is_layout_complete(self.server_list[0], self.vol_name,
                                        dirpath='/testdir')
        if ret:
            raise Exception(f"Unexpected: Volume {self.vol_name} layout is"
                            " complete")

        # Start Rebalance fix-layout
        redant.rebalance_start(self.vol_name, self.server_list[0],
                               fix_layout=True)

        # Wait for fix-layout to complete
        ret = redant.wait_for_fix_layout_to_complete(self.server_list[0],
                                                     self.vol_name)
        if not ret:
            raise Exception(f"Volume {self.vol_name}: Fix-layout is either "
                            "failed or in-progress")

        # DHT Layout validation
        ret = redant.validate_files_in_dir(self.client_list[0],
                                           self.mountpoint,
                                           test_type=TEST_LAYOUT_IS_COMPLETE,
                                           file_type=FILETYPE_DIRS)
        if not ret:
            raise Exception("LAYOUT_IS_COMPLETE: FAILED")
