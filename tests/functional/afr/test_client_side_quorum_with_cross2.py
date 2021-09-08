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
    TC to verify the client side quorum Test Cases with cross 2 volume
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
        conf_hash = self.vol_type_inf[self.volume_type].copy()
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

    def run_test(self, redant):
        """
        Test Script to verify the Client Side Quorum with auto option
        * set cluster.quorum-type to auto.
        * start I/O from the mount point.
        * kill 2-nd brick process from the each and every replica set
        * perform ops
        """
        script_file_path = "/usr/share/redant/script/file_dir_ops.py"
        # set cluster.quorum-type to auto
        options = {"cluster.quorum-type": "auto"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Start IO on mounts
        all_mounts_procs = []
        redant.logger.info("Starting IO on mountpoint...")
        cmd = (f"python3 {script_file_path} create_files -f 10"
               f" --base-file-name file {self.mountpoint}")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Validate IO
        ret = redant.validate_io_procs(all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # get the subvolumes
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        num_subvols = len(subvols)

        # bring 2-nd bricks offline for all the subvolumes
        offline_bricks = []
        for i in range(0, num_subvols):
            subvol_brick_list = subvols[i]
            bricks_to_bring_offline = subvol_brick_list[1]
            if not redant.bring_bricks_offline(self.vol_name,
                                               bricks_to_bring_offline):
                raise Exception("Failed to bring down the bricks. Please "
                                "check the log file for more details.")
            offline_bricks.append(bricks_to_bring_offline)

        # create new file named newfile0.txt
        all_mounts_procs = []
        redant.logger.info("Creating new file on mountpoint...")
        cmd = (f"python3 {script_file_path} create_files -f 1 --base-file-name"
               f" newfile {self.mountpoint}")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("Creating files failed")

        # create directory user1
        all_mounts_procs = []
        redant.logger.info("Start creating directory on mountpoint...")
        cmd = f"python3 {script_file_path} create_deep_dir {self.mountpoint}"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("Creating directory failed")

        # create h/w link to file
        redant.logger.info("Start creating hard link for file0.txt on mount")
        cmd = (f"ln {self.mountpoint}/file0.txt {self.mountpoint}/"
               "file0.txt_hwlink")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # create s/w link
        redant.logger.info("Start creating soft link for file1.txt on mount")
        cmd = (f"ln -s {self.mountpoint}/file1.txt {self.mountpoint}/"
               "file1.txt_swlink")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # append to file
        redant.logger.info("Appending to file1.txt on mountpoint")
        cmd = (f"cat {self.mountpoint}/file0.txt >> {self.mountpoint}/"
               "file1.txt")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # modify the file
        redant.logger.info("Modifying file1.txt on mountpoint")
        cmd = f"echo 'Modify Contents' > {self.mountpoint}/file1.txt"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # truncate the file
        redant.logger.info("Truncating file1.txt on mountpoint")
        cmd = f"truncate -s 0 {self.mountpoint}/file1.txt"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # read the file
        redant.logger.info("Starting reading files on mountpoint")
        all_mounts_procs = []
        cmd = f"python3 {script_file_path} read {self.mountpoint}"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("Reading failed")

        # stat on file
        redant.logger.info("Stat on file1.txt on mountpoint")
        cmd = f"stat {self.mountpoint}/file1.txt"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # stat on dir
        redant.logger.info("Stat on directory on mountpoint")
        cmd = f"stat {self.mountpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # ls on mount point
        redant.logger.info("ls on mount point")
        cmd = f"ls {self.mountpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # bring back the bricks online for all subvolumes
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_bricks):
            raise Exception(f"Failed to bring the brick {offline_bricks} "
                            "online")
