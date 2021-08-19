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
    TC to verify the client side quorum with fixed option with cross 2 volume
"""

# disruptive;rep,dist-rep
# TODO: nfs
from tests.d_parent_test import DParentTest


class TestClientSideQuorumCross2Tests(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        conf_hash['replica_count'] = 2
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

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

    def _perform_read_write_io_with_rofs(self, filename, mounts):
        """
        Perform write and read IO on mountpoint, in which write must fail
        with ROFS.
        """
        # Start IO (write/read), read must succeed, but write should fail
        all_mounts_procs = []
        self.redant.logger.info("Creating new file on mountpoint...")
        cmd = (f"python3 /tmp/file_dir_ops.py create_files -f 10"
               f" --base-file-name {filename} {self.mounts['mountpath']}")
        proc = self.redant.execute_command_async(cmd, self.mounts['client'])
        all_mounts_procs.append(proc)

        # Validate IO
        ret = self.redant.is_io_procs_fail_with_rofs(all_mounts_procs, mounts)
        if not ret:
            raise Exception("Unexpected Error and IO successful"
                            " on Read-Only File System")

        # Read files on mountpoint
        self.redant.logger.info("Starting reading files on mountpoint")
        all_mounts_procs = []
        cmd = f"python3 /tmp/file_dir_ops.py read {self.mounts['mountpath']}"
        proc = self.redant.execute_command_async(cmd, self.mounts['client'])
        all_mounts_procs.append(proc)

        # Validate IO
        ret, _ = self.redant.validate_io_procs(all_mounts_procs, mounts)
        if not ret:
            raise Exception("Reading failed")

    def run_test(self, redant):
        """
        Test Script to verify the Client Side Quorum with fixed
        for cross 2 volume

        * Disable self heal daemom
        * set cluster.quorum-type to fixed.
        * start I/O( write and read )from the mount point - must succeed
        * Bring down brick1
        * start I/0 ( write and read ) - must succeed
        * set the cluster.quorum-count to 1
        * start I/0 ( write and read ) - must succeed
        * set the cluster.quorum-count to 2
        * start I/0 ( write and read ) - read must pass, write will fail
        * bring back the brick1 online
        * start I/0 ( write and read ) - must succeed
        * Bring down brick2
        * start I/0 ( write and read ) - read must pass, write will fail
        * set the cluster.quorum-count to 1
        * start I/0 ( write and read ) - must succeed
        * cluster.quorum-count back to 2 and cluster.quorum-type to auto
        * start I/0 ( write and read ) - must succeed
        * Bring back brick2 online
        * Bring down brick1
        * start I/0 ( write and read ) - read must pass, write will fail
        * set the quorum-type to none
        * start I/0 ( write and read ) - must succeed
        """
        # Disable self heal daemon
        options = {"cluster.self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # set cluster.quorum-type to fixed
        options = {"cluster.quorum-type": "fixed"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Start IOO on mounts
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        self._perform_read_write_io("file", self.mounts)

        # get the subvolumes
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        num_subvols = len(subvols)

        # Bring down brick1 for all the subvolumes
        subvolumes_first_brick_list = []
        subvolumes_second_brick_list = []
        for i in range(0, num_subvols):
            subvol_brick_list = subvols[i]
            subvolumes_first_brick_list.append(subvol_brick_list[0])
            subvolumes_second_brick_list.append(subvol_brick_list[1])

        if not redant.bring_bricks_offline(self.vol_name,
                                           subvolumes_first_brick_list):
            raise Exception("Failed to bring down the bricks. Please "
                            "check the log file for more details.")

        # Start IO (write/read), must succeed
        self._perform_read_write_io("second_file", self.mounts)

        # set the cluster.quorum-count to 1
        options = {"cluster.quorum-count": "1"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Start IO (write/read), must succeed
        self._perform_read_write_io("third_file", self.mounts)

        # set the cluster.quorum-count to 2
        options = {"cluster.quorum-count": "2"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Start IO (write/read), write will fail, read must succeed
        self._perform_read_write_io_with_rofs("fourth_file", self.mounts)

        # bring back the brick1 online for all subvolumes
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          subvolumes_first_brick_list):
            raise Exception("Failed to bring the brick "
                            f"{subvolumes_first_brick_list} online")

        # Start IO (write/read), must succeed
        self._perform_read_write_io("fifth_file", self.mounts)

        # bring down brick2 of all subvolumes
        if not redant.bring_bricks_offline(self.vol_name,
                                           subvolumes_second_brick_list):
            raise Exception("Failed to bring down the bricks. Please "
                            "check the log file for more details.")

        # Start IO (write/read), write will fail, read must succeed
        self._perform_read_write_io_with_rofs("sixth_file", self.mounts)

        # set the cluster.quorum-count to 1
        options = {"cluster.quorum-count": "1"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Start IO (write/read), must succeed
        self._perform_read_write_io("seventh_file", self.mounts)

        # set the cluster.quorum-count to 2, and quorum-type to auto
        options = {"cluster.quorum-type": "auto",
                   "cluster.quorum-count": "1"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Start IO (write/read), must succeed
        self._perform_read_write_io("eight_file", self.mounts)

        # bring back the brick2 online for all subvolumes
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          subvolumes_second_brick_list):
            raise Exception("Failed to bring the brick "
                            f"{subvolumes_first_brick_list} online")

        # bring down brick1 of all subvolumes again
        if not redant.bring_bricks_offline(self.vol_name,
                                           subvolumes_first_brick_list):
            raise Exception("Failed to bring down the bricks. Please "
                            "check the log file for more details.")

        # Start IO (write/read), write will fail, read must succeed
        self._perform_read_write_io_with_rofs("nineth_file", self.mounts)

        # set the cluster.quorum-type to none
        options = {"cluster.quorum-type": "none"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Start IO (write/read), must succeed
        self._perform_read_write_io("tenth_file", self.mounts)

        # bring back the brick1 online for all subvolumes
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          subvolumes_first_brick_list):
            raise Exception("Failed to bring the brick "
                            f"{subvolumes_first_brick_list} online")
