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
    TC to check copy of a dir when dest_dir present or not
"""

# disruptive;rep,dist,dist-rep,arb,dist-arb,disp,dist-disp
from common.ops.gluster_ops.constants import \
    (TEST_FILE_EXISTS_ON_HASHED_BRICKS, TEST_LAYOUT_IS_COMPLETE)
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestDhtCopy(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Skip for upstream installation for disp,dist-disp vol
        if self.volume_type == "dist-disp" or self.volume_type == "disp":
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

    def _copy_dir(self):
        """
        Copy direcotry and check correctness of layout
        """
        # Create multiple directories
        self.redant.create_dir(self.mountpoint, "root_dir/test_dir{1..3}",
                               self.client_list[0])

        cmd = f"ls {self.mountpoint}/root_dir"
        ret = self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        list_of_created_dirs = "".join(ret['msg']).split('\n')
        flag = True
        for x_count in range(3):
            dir_name = f'test_dir{x_count + 1}'
            if dir_name not in list_of_created_dirs:
                flag = False
        if not flag:
            raise Exception("ls command didn't list all the directories")

        # Create files at different directory levels
        cmd = f"touch {self.mountpoint}/root_dir/test_file{{1..5}}"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f"ls {self.mountpoint}/root_dir"
        ret = self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        list_of_files_and_dirs = "".join(ret['msg']).split('\n')
        flag = True
        for x_count in range(3):
            dir_name = f'test_dir{x_count + 1}'
            if dir_name not in list_of_files_and_dirs:
                flag = False
        for x_count in range(5):
            file_name = f'test_file{x_count + 1}'
            if file_name not in list_of_files_and_dirs:
                flag = False
        if not flag:
            raise Exception("ls command didn't list all the directories")

        if not self.destination_exists:
            destination_dir = 'root_dir_1'
        else:
            self.redant.create_dir(self.mountpoint, "new_dir",
                                   self.client_list[0])
            destination_dir = 'new_dir/root_dir'

        # Performing layout checks for root_dir
        flag = (self.redant.validate_files_in_dir(
                self.client_list[0], f"{self.mountpoint}/root_dir",
                test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS))
        if not ret:
            raise Exception("root directory not present on every brick")

        ret = (self.redant.validate_files_in_dir(
               self.client_list[0], f"{self.mountpoint}/root_dir",
               test_type=TEST_LAYOUT_IS_COMPLETE))
        if not ret:
            raise Exception("layout of every directory is not complete")

        # Copying root_dir at the mount point
        cmd = (f"cp -r {self.mountpoint}/root_dir "
               f"{self.mountpoint}/{destination_dir}")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Performing layout checks for copied directory
        ret = (self.redant.validate_files_in_dir(
               self.client_list[0], f"{self.mountpoint}/{destination_dir}",
               test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS))
        if not ret:
            raise Exception("directories not present on every brick")

        ret = (self.redant.validate_files_in_dir(
               self.client_list[0], f"{self.mountpoint}/{destination_dir}",
               test_type=TEST_LAYOUT_IS_COMPLETE))
        if not ret:
            raise Exception("layout of every directory is not complete")

        # Listing the copied directory
        cmd = f"ls -A1 {self.mountpoint}/{destination_dir}"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Copied directory listed
        cmd = f"ls -A1 {self.mountpoint}/root_dir"
        ret1 = self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f"ls -A1 {self.mountpoint}/{destination_dir}"
        ret2 = self.redant.execute_abstract_op_node(cmd, self.client_list[0])
        if ret1['msg'] != ret2['msg']:
            raise Exception("contents and attributes of original and "
                            "copied directory not same")

        # Listing the copied directory on all the subvolumes
        brick_list = self.redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
        if not brick_list:
            raise Exception("Failed to ge the brick list")

        for brick in brick_list:
            host_addr, brick_path = brick.split(':')

            cmd = f"ls -A1 {brick_path}/{destination_dir}"
            self.redant.execute_abstract_op_node(cmd, host_addr)

            cmd = f"ls -l --time-style=\'+\' {brick_path}/root_dir/ | grep ^d"
            ret1 = self.redant.execute_abstract_op_node(cmd, host_addr)

            cmd = (f"ls -l --time-style=\'+\' {brick_path}/{destination_dir}"
                   " | grep ^d")
            ret2 = self.redant.execute_abstract_op_node(cmd, host_addr)
            if ret1['msg'] != ret2['msg']:
                raise Exception("contents and attributes of original and "
                                "copied directory not same on brick "
                                f"{brick}")

    def run_test(self, redant):
        """
        Steps:
        - Create a parent directory and subdirectories at mount point.
        - After that create a copy of parent directory at mount point
        - First when destination directory is not there, and then do again
          after creating destination directory for copying.
        - In the first test, contents will be copied from one directory
          to another.
        - In the second test case, entire directory will be copied to another
          directory along with the contents.
        - Then it checks for correctness of layout and content of source and
          copied directory at all sub-vols.
        """
        # Checking when destination directory for copying directory doesn't
        # exist
        self.destination_exists = False
        self._copy_dir()

        # Checking by creating destination directory first and then copying
        # created directory
        self.destination_exists = True
        self._copy_dir()
