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
    TC to verify that if a file is picked for migration and then deleted, the
    file should be removed successfully.
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
from tests.d_parent_test import DParentTest


class TestDeleteFileInMigration(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        * First create a big data file of 10GB.
        * Rename that file, such that after rename a linkto file is created
          (we are doing this to make sure that file is picked for migration.)
        * Add bricks to the volume and trigger rebalance using force option.
        * When the file has been picked for migration, delete that file from
          the mount point.
        * Check whether the file has been deleted or not on the mount-point
          as well as the back-end bricks.
        """
        # Location of source file
        src_file = f"{self.mountpoint}/file1"

        # Finding a file name such that renaming source file to it will form a
        # linkto file
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols")

        newhash = redant.find_new_hashed(subvols, "", "file1")
        if not newhash:
            raise Exception("Failed to find new hash")

        new_name = str(newhash[0])
        new_host, new_name_path = newhash[1].split(':')
        new_name_path = new_name_path[:-1]

        # Location of destination file to which source file will be renamed
        dst_file = f'{self.mountpoint}/{new_name}'

        # Create a 10GB file source file
        cmd = f"dd if=/dev/urandom of={src_file} bs=1024K count=10000"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Move file such that it hashes to some other subvol and forms linkto
        # file
        ret = redant.move_file(self.client_list[0], src_file, dst_file)
        if not ret:
            raise Exception("Rename failed")

        # Check if "file_two" is linkto file
        ret = redant.is_linkto_file(new_host, f'{new_name_path}/{new_name}')
        if not ret:
            raise Exception("File is not a linkto file")

        # Expanding volume by adding bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=True)
        if not ret:
            raise Exception("Volume expansion failed")

        # Log Volume Info and Status after expanding the volume
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Failed to log volume info and status")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0], force=True)

        # Check if rebalance is running and delete the file
        status_info = redant.get_rebalance_status(self.vol_name,
                                                  self.server_list[0])
        status = status_info['aggregate']['statusStr']
        if status != "in progress":
            raise Exception("Rebalance is not running")

        redant.execute_abstract_op_node(f"rm -rf {dst_file}",
                                        self.client_list[0])

        # Check if the file is present on the mount point
        ret = redant.execute_abstract_op_node(f"ls -l {dst_file}",
                                              self.client_list[0], False)
        if ret['error_code'] != 2:
            raise Exception(f"Failed to delete file {dst_file}")

        # Check if the file is present on the backend bricks
        bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not bricks:
            raise Exception("Failed to get the brick list")

        for brick in bricks:
            node, brick_path = brick.split(':')
            cmd = f"ls -l {brick_path}/{new_name}"
            ret = redant.execute_abstract_op_node(cmd, node, False)
            if ret['error_code'] != 2:
                raise Exception("File is still present on"
                                f" back-end brick: {brick_path}")

        # Check if rebalance process is still running
        for server in self.server_list:
            ret = redant.execute_abstract_op_node("pgrep rebalance", server,
                                                  False)
            if ret['error_code'] != 1:
                raise Exception("Rebalance process is still running on "
                                f"server {server}")
