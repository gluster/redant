"""
 Copyright (C) 2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check that the custom xattrs are healed on the
    dirs when new bricks are added
"""

# disruptive;dist-rep,dist-disp,dist-arb
from common.ops.gluster_ops.constants import TEST_LAYOUT_IS_COMPLETE
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestCustomxattrsOnNewBricks(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Skip for upstream installation for dist-disp vol
        if self.volume_type == "dist-disp":
            self.redant.check_gluster_installation(self.server_list,
                                                   "downstream")

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def _check_xattr(self, list_of_all_dirs):
        """
        Check the custom xattr on backend bricks for the directories.
        """
        brick_list = self.redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
        if not brick_list:
            raise Exception("Failed to get brick list")

        for direc in list_of_all_dirs:
            for brick in brick_list:
                host, brick_path = brick.split(':')
                brick_dir_path = f"{brick_path}/{direc}"
                self.redant.get_fattr(brick_dir_path, 'user.foo', host)

    def run_test(self, redant):
        """
        Steps :
        1) Create a volume.
        2) Mount the volume using FUSE.
        3) Create 100 directories on the mount point.
        4) Set the xattr on the directories.
        5) Add bricks to the volume and trigger rebalance.
        6) Check if all the bricks have healed.
        7) After rebalance completes, check the xattr for dirs on the newly
           added bricks.
        """
        # Creating 1000 directories on volume root
        redant.create_dir(self.mountpoint, "dir{1..100}", self.client_list[0])

        # Lookup on the mount point
        cmd = f'ls {self.mountpoint}/'
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Setting up the custom xattr for all the directories on mount point
        cmd = f'setfattr -n user.foo -v "foobar" {self.mountpoint}/dir*'
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Checking the layout of the directories on the back-end
        flag = redant.validate_files_in_dir(self.client_list[0],
                                            self.mountpoint,
                                            test_type=TEST_LAYOUT_IS_COMPLETE)
        if not flag:
            raise Exception("Layout has some holes or overlaps")

        # Creating a list of directories on the mount point
        list_of_all_dirs = redant.get_dir_contents(self.mountpoint,
                                                   self.client_list[0])
        if not list_of_all_dirs:
            raise Exception("Creation of directory list failed.")

        # Checking the custom xattr on backend bricks for the directories
        self._check_xattr(list_of_all_dirs)

        # Expanding volume by adding bricks to the volume
        force = False
        if self.volume_type == "dist-disp":
            force = True
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots, force)
        if not ret:
            raise Exception("Volume expand failed")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0])
        if not ret:
            raise Exception(f"Volume {self.vol_name}: Rebalance failed "
                            "to complete")

        # Lookup on the mount point
        cmd = f'ls -laR {self.mountpoint}/'
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check if all the bricks are healed
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name,
                                              timeout_period=900):
            raise Exception("Heal not yet completed")

        # Checking the custom xattrs for all the directories on
        # back end bricks after rebalance is complete
        self._check_xattr(list_of_all_dirs)
