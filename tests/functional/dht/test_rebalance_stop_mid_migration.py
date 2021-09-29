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
    This test case creates a large file at mount point,
    adds extra brick and initiates rebalance. While
    migration is in progress, it stops rebalance process
    and checks if it has stopped.
"""

# disruptive;dist,rep,arb,disp,dist-rep,dist-arb,dist-disp
from common.ops.gluster_ops.constants import \
    (FILETYPE_FILES, TEST_FILE_EXISTS_ON_HASHED_BRICKS,
     TEST_LAYOUT_IS_COMPLETE)
from tests.d_parent_test import DParentTest


class TestDhtClass(DParentTest):

    def run_test(self, redant):
        """
        Testcase Steps:
        1. Create and start a volume.
        2. Mount volume on client and create a large file.
        3. Add bricks to the volume and check layout
        4. Rename the file such that it hashs to different
           subvol.
        5. Start rebalance on volume.
        6. Stop rebalance on volume.
        """
        # Create file BIG1.
        cmd = (f"dd if=/dev/urandom of={self.mountpoint}/BIG1 "
               "bs=1024K count=10000")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Checking if file created on correct subvol or not.
        ret = (redant.validate_files_in_dir(
               self.client_list[0], self.mountpoint,
               test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS,
               file_type=FILETYPE_FILES))
        if not ret:
            raise Exception("Files not created on correct sub-vols")

        # Adding brick to volume
        brick_list = redant.form_brick_cmd_to_add_brick(self.server_list[0],
                                                        self.vol_name,
                                                        self.server_list,
                                                        self.brick_roots)
        if brick_list is None:
            raise Exception("Failed to form brick list to add brick")

        redant.add_brick(self.vol_name, brick_list, self.server_list[0],
                         force=True)

        # Check if brick is added successfully or not.
        current_bricks = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])

        brick_list = brick_list.split(" ")
        for brick in brick_list:
            if brick not in current_bricks:
                raise Exception(f"Brick {brick} is not added to volume")

        # Create directory testdir.
        cmd = (f'cd {self.mountpoint} ; mkdir testdir;')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Layout should be set on the new brick and should be
        # continous and complete
        ret = redant.validate_files_in_dir(self.client_list[0],
                                           f"{self.mountpoint}/testdir",
                                           test_type=TEST_LAYOUT_IS_COMPLETE)
        if not ret:
            raise Exception("LAYOUT_IS_COMPLETE: FAILED")

        # Rename file so that it gets hashed to different subvol
        file_index = 0
        path_info_dict = redant.get_pathinfo(f"{self.mountpoint}/BIG1",
                                             self.client_list[0])
        initial_brick_set = path_info_dict['brickdir_paths']

        while True:
            # Calculate old_filename and new_filename and rename.
            file_index += 1
            old_filename = f"{self.mountpoint}/BIG{file_index}"
            new_filename = f"{self.mountpoint}/BIG{file_index+1}"
            cmd = f"mv {old_filename} {new_filename}"
            redant.execute_abstract_op_node(cmd, self.client_list[0])
            # Checking if it was moved to new subvol or not.
            path_info_dict = (redant.get_pathinfo(
                              f"{self.mountpoint}/BIG{file_index+1}",
                              self.client_list[0]))
            if path_info_dict['brickdir_paths'] != initial_brick_set:
                break

        # Start rebalance on volume
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Stop rebelance on volume
        redant.rebalance_stop(self.vol_name, self.server_list[0])

        # Get rebalance status in xml
        cmd = (f"gluster volume rebalance {self.vol_name} status --xml")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Rebalance still running "
                            "even after stop.")
