"""
 Copyright (C) 2018-2020 Red Hat, Inc. http://www.redhat.com>

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
    TC to induce holes in layout by remove brick force then lookup to
    fix layout
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
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
        # Minimum of 2 clients are needed
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=2)

        # Skip for upstream installation for dist-disp vol
        if self.volume_type == "dist-disp":
            self.redant.check_gluster_installation(self.server_list,
                                                   "downstream")

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        if conf_hash['dist_count'] <= 2:
            conf_hash['dist_count'] = 4

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
        Steps :
        1) Create a volume and mount it using FUSE.
        2) Create a directory "testdir" on mount point.
        3) Check if the layout is complete.
        4) Log volume info and status before remove-brick operation.
        5) Form a list of bricks to be removed.
        6) Start remove-brick operation using 'force'.
        7) Let remove-brick complete and check layout.
        8) Mount the volume on a new mount.
        9) Send a lookup on mount point.
        10) Check if the layout is complete.
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

        # Form bricks list for Shrinking volume
        bricks_list_to_remove = (redant.form_bricks_list_to_remove_brick(
                                 self.server_list[0], self.vol_name,
                                 subvol_num=1))

        if bricks_list_to_remove is None:
            raise Exception("Failed to form bricks list to remove-brick. "
                            f"Hence unable to shrink volume {self.vol_name}")

        # Shrink volume
        redant.remove_brick(self.server_list[0], self.vol_name,
                            bricks_list_to_remove, "force")

        # Check the layout
        ret = redant.is_layout_complete(self.server_list[0], self.vol_name,
                                        dirpath='/testdir')
        if ret:
            raise Exception(f"Unexpected: Volume {self.vol_name} layout is"
                            " complete")

        # Mount the volume on a new mount point
        redant.execute_abstract_op_node(f"mkdir  -p {self.mountpoint}",
                                        self.client_list[1])

        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[1])

        # Send a look up on the directory
        cmd = f'ls {self.mountpoint}/testdir'
        redant.execute_abstract_op_node(cmd, self.client_list[1])

        # DHT Layout validation
        ret = redant.validate_files_in_dir(self.client_list[1],
                                           f"{self.mountpoint}/testdir",
                                           test_type=TEST_LAYOUT_IS_COMPLETE,
                                           file_type=FILETYPE_DIRS)
        if not ret:
            raise Exception("LAYOUT_IS_COMPLETE: FAILED")
