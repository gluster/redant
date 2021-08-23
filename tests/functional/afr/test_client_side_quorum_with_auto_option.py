"""
 Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module tests the client side quorum.
"""

# disruptive;rep,dist-rep
# TODO: nfs
from tests.d_parent_test import DParentTest


class TestClientSideQuorumTests(DParentTest):

    def run_test(self, redant):
        """
        Test Script to verify the Client Side Quorum with auto option

        * set cluster.quorum-type to auto.
        * start I/O from the mount point.
        * kill 2 of the brick process from the each and every replica set
        * perform ops
        """
        # set cluster.quorum-type to auto
        options = {"cluster.quorum-type": "auto"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # write files on all mounts
        redant.logger.info("Starting IO on all mounts...")
        cmd = (f"python3 /tmp/file_dir_ops.py create_files "
               f"-f 10 --base-file-name file {self.mountpoint}")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # get the subvolumes
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        num_subvols = len(subvols)

        # bring bricks offline( 2 bricks ) for all the subvolumes
        for i in range(0, num_subvols):
            subvol_brick_list = subvols[i]
            bricks_to_bring_offline = subvol_brick_list[0:2]
            if not redant.bring_bricks_offline(self.vol_name,
                                               bricks_to_bring_offline):
                raise Exception("Failed to bring down the bricks. Please "
                                "check the log file for more details.")

        # create a file test_file
        # cannot use python module here since we need the stderr output
        all_mounts_procs = []
        cmd = (f"dd if=/dev/urandom of={self.mountpoint}/test_file bs=1M "
               "count=1")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # create directory user1
        all_mounts_procs = []
        cmd = f"mkdir {self.mountpoint}/user1 "
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # create h/w link to file
        all_mounts_procs = []
        cmd = (f"ln {self.mountpoint}/file0.txt {self.mountpoint}/"
               "file0.txt_hwlink")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # create s/w link
        all_mounts_procs = []
        cmd = (f"ln -s {self.mountpoint}/file1.txt {self.mountpoint}/"
               "file1.txt_swlink")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # append to file
        all_mounts_procs = []
        cmd = (f"cat {self.mountpoint}/file0.txt >> {self.mountpoint}/"
               "file1.txt")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # modify the file
        all_mounts_procs = []
        cmd = f"echo 'Modify Contents' > {self.mountpoint}/file1.txt"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # truncate the file
        all_mounts_procs = []
        cmd = f"truncate -s 0 {self.mountpoint}/file1.txt"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # read the file
        all_mounts_procs = []
        cmd = f"cat {self.mountpoint}/file1.txt"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # stat on file
        all_mounts_procs = []
        cmd = f"stat {self.mountpoint}/file1.txt"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # stat on dir
        all_mounts_procs = []
        cmd = f"stat {self.mountpoint}"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")

        # ls on mount point
        all_mounts_procs = []
        cmd = f"ls {self.mountpoint}"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                    self.mounts)
        if not ret:
            raise Exception("Unexpected error and IO successful"
                            " on not connected transport endpoint")
