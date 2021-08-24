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
    Test Cases in this module tests the client side quorum in cross 3 volume
"""

# disruptive;rep,dist-rep
from tests.d_parent_test import DParentTest


class TestClientSideQuorumTestsWithSingleVolumeCross3(DParentTest):

    def _perform_read_write_io(self, filename, mounts):
        """
        Perform write and read IO on mountpoint
        """
        # Start IO (write/read), must succeed
        all_mounts_procs = []
        self.redant.logger.info("Creating new file on mountpoint...")
        cmd = (f"python3 /tmp/file_dir_ops.py create_files -f 10"
               f" --base-file-name {filename} {self.mounts['mountpath']}")
        proc = self.redant.execute_command_async(cmd, self.mounts['client'])
        all_mounts_procs.append(proc)

        # Validate IO
        ret = self.redant.validate_io_procs(all_mounts_procs, mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Read files on mountpoint
        self.redant.logger.info("Starting reading files on mountpoint")
        all_mounts_procs = []
        cmd = f"python3 /tmp/file_dir_ops.py read {self.mounts['mountpath']}"
        proc = self.redant.execute_command_async(cmd, self.mounts['client'])
        all_mounts_procs.append(proc)

        # Validate IO
        ret = self.redant.validate_io_procs(all_mounts_procs, mounts)
        if not ret:
            raise Exception("Reading failed")

    def _perform_read_write_io_with_error(self, filename, mounts):
        """
        Perform write and read IO on mountpoint, in which must fail
        with not connected transport endpoint.
        """
        # Start IO (write/read), should fail
        all_mounts_procs = []
        self.redant.logger.info("Creating new file on mountpoint...")
        cmd = (f"dd if=/dev/urandom of={self.mounts['mountpath']}/{filename}"
               " bs=1M count=1")
        proc = self.redant.execute_command_async(cmd, self.mounts['client'])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = self.redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                         mounts)
        if not ret:
            raise Exception("Unexpected Error and IO successful"
                            " on not connected transport endpoint")

        # Read files on mountpoint should fail
        self.redant.logger.info("Starting reading files on mountpoint")
        all_mounts_procs = []
        cmd = f"cat {self.mounts['mountpath']}/file1.txt"
        proc = self.redant.execute_command_async(cmd, self.mounts['client'])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = self.redant.is_io_procs_fail_with_error(all_mounts_procs,
                                                         mounts)
        if not ret:
            raise Exception("Unexpected Error and Read successful"
                            " on not connected transport endpoint")

    def run_test(self, redant):
        """
        Test Script to verify the Client Side Quorum with fixed
        for cross 3 volume

        * Disable self heal daemom
        * set cluster.quorum-type to fixed.
        * start I/O( write and read )from the mount point - must succeed
        * Bring down brick1
        * start I/0 ( write and read ) - must succeed
        * Bring down brick2
        * start I/0 ( write and read ) - must succeed
        * set the cluster.quorum-count to 1
        * start I/0 ( write and read ) - must succeed
        * set the cluster.quorum-count to 2
        * start I/0 ( write and read ) - read and write will fail
        * bring back the brick1 online
        * start I/0 ( write and read ) - must succeed
        * Bring back brick2 online
        * start I/0 ( write and read ) - must succeed
        * set cluster.quorum-type to auto
        * start I/0 ( write and read ) - must succeed
        * Bring down brick1 and brick2
        * start I/0 ( write and read ) - read and write will fail
        * set the cluster.quorum-count to 1
        * start I/0 ( write and read ) - read and write will fail
        * set the cluster.quorum-count to 3
        * start I/0 ( write and read ) - read and write will fail
        * set the quorum-type to none
        * start I/0 ( write and read ) - must succeed
        """
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        # Disable self heal daemon
        options = {"cluster.self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # set cluster.quorum-type to fixed
        options = {"cluster.quorum-type": "fixed"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # start I/O( write ) - must succeed
        self._perform_read_write_io("file", self.mounts)

        # get the subvolumes
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        num_subvols = len(subvols)

        # bring down brick1 for all the subvolumes
        offline_brick1_from_replicasets = []
        for i in range(0, num_subvols):
            subvol_brick_list = subvols[i]
            brick_to_bring_offline1 = subvol_brick_list[0]
            if not redant.bring_bricks_offline(self.vol_name,
                                               brick_to_bring_offline1):
                raise Exception("Failed to bring down the bricks. Please "
                                "check the log file for more details.")
            offline_brick1_from_replicasets.append(brick_to_bring_offline1)

        # start I/0 ( write and read ) - must succeed
        self._perform_read_write_io("testfile", self.mounts)

        # bring down brick2 for all the subvolumes
        offline_brick2_from_replicasets = []
        for i in range(0, num_subvols):
            subvol_brick_list = subvols[i]
            brick_to_bring_offline2 = subvol_brick_list[1]
            if not redant.bring_bricks_offline(self.vol_name,
                                               brick_to_bring_offline2):
                raise Exception("Failed to bring down the bricks. Please "
                                "check the log file for more details.")
            offline_brick2_from_replicasets.append(brick_to_bring_offline2)

        # start I/0 ( write and read ) - must succeed
        self._perform_read_write_io("newfile", self.mounts)

        # set the cluster.quorum-count to 1
        options = {"cluster.quorum-count": "1"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # start I/0 ( write and read ) - must succeed
        self._perform_read_write_io("filename", self.mounts)

        # set the cluster.quorum-count to 2
        options = {"cluster.quorum-count": "2"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # start I/0 ( write and read ) - read and write will fail
        self._perform_read_write_io_with_error("test_file", self.mounts)

        # bring back the brick1 online for all subvolumes
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick1_from_replicasets):
            raise Exception("Failed to bring the brick "
                            f"{offline_brick1_from_replicasets} online")

        # start I/0 ( write and read ) - must succeed
        self._perform_read_write_io("newfilename", self.mounts)

        # Bring back brick2 online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick2_from_replicasets):
            raise Exception("Failed to bring the brick "
                            f"{offline_brick2_from_replicasets} online")

        # start I/0 ( write and read ) - must succeed
        self._perform_read_write_io("textfile", self.mounts)

        # set cluster.quorum-type to auto
        options = {"cluster.quorum-type": "auto"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # start I/0 ( write and read ) - must succeed
        self._perform_read_write_io("newtextfile", self.mounts)

        # bring down brick1 and brick2 for all the subvolumes
        brick_to_bring_offline = []
        for i in range(0, num_subvols):
            subvol_brick_list = subvols[i]
            brick_to_bring_offline = subvol_brick_list[0:2]
            if not redant.bring_bricks_offline(self.vol_name,
                                               brick_to_bring_offline):
                raise Exception("Failed to bring down the bricks. Please "
                                "check the log file for more details.")

        # start I/0 ( write and read ) - read and write will fail
        self._perform_read_write_io_with_error("new_test_file", self.mounts)

        # set the cluster.quorum-count to 1
        options = {"cluster.quorum-count": "1"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # start I/0 ( write and read ) - read and write will fail
        self._perform_read_write_io_with_error("new_test_file", self.mounts)

        # set the cluster.quorum-count to 3
        options = {"cluster.quorum-count": "3"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # start I/0 ( write and read ) - read and write will fail
        self._perform_read_write_io_with_error("new_test_file", self.mounts)

        # set the quorum-type to none
        options = {"cluster.quorum-type": "none"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # start I/0 ( write and read ) - must succeed
        self._perform_read_write_io("lastfile", self.mounts)
