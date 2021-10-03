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
    TC to check that all directories are read
    and listed while rebalance is still in progress.
"""

# disruptive;dist,rep,disp,arb,dist-rep,dist-arb,dist-disp
from tests.d_parent_test import DParentTest


class TestReaddirpWithRebalance(DParentTest):

    def run_test(self, redant):
        """
        Steps :
        1) Create a volume.
        2) Mount the volume using FUSE.
        3) Create a dir "master" on mount-point.
        4) Create 8000 empty dirs (dir1 to dir8000) inside dir "master".
        5) Now inside a few dirs (e.g. dir1 to dir10), create deep dirs
           and inside every dir, create 50 files.
        6) Collect the number of dirs present on /mnt/<volname>/master
        7) Change the rebalance throttle to lazy.
        8) Add-brick to the volume (at least 3 replica sets.)
        9) Start rebalance using "force" option on the volume.
        10) List the directories on dir "master".
        """
        # Start IO on mounts
        redant.create_dir(self.mountpoint, "master", self.client_list[0])

        # Create 8000 empty dirs
        file_dir_script = "/usr/share/redant/script/file_dir_ops.py"
        cmd = (f"ulimit -n 64000; python3 {file_dir_script} create_deep_dir"
               f" --dir-length 8000 --dir-depth 0 {self.mountpoint}/master/")
        proc = redant.execute_command_async(cmd, self.client_list[0])

        # Validate 8000 empty dirs are created successfully
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        if not redant.validate_io_procs(proc, self.mounts):
            raise Exception("IO failed on some of the clients")

        # Create deep dirs and files
        cmd = (f"python3 {file_dir_script} create_deep_dirs_with_files"
               " --dir-length 10 --dir-depth 1 --max-num-of-dirs 50 "
               " --num-of-files 50 --file-type empty-file"
               f" {self.mountpoint}/master/")
        proc = redant.execute_command_async(cmd, self.client_list[0])

        # Validate deep dirs and files are created successfully
        if not redant.validate_io_procs(proc, self.mounts):
            raise Exception("IO failed on some of the clients")

        # Check the dir count before rebalance
        cmd = f'cd {self.mountpoint}/master; ls -l | wc -l'
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        dir_count_before = int(ret['msg'][0].strip())

        # Change the rebalance throttle to lazy
        redant.set_rebalance_throttle(self.vol_name, self.server_list[0],
                                      throttle_type='lazy')

        # Add-bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   distribute_count=3, force=True)
        if not ret:
            raise Exception("Failed to add-brick to the volume")

        # Start rebalance using force
        redant.rebalance_start(self.vol_name, self.server_list[0], force=True)

        # Check if rebalance is in progress
        rebalance_status = redant.get_rebalance_status(self.vol_name,
                                                       self.server_list[0])
        if rebalance_status['aggregate']['statusStr'] != "in progress":
            raise Exception("Rebalance is not in 'in progress' state,"
                            " either rebalance is in compeleted state"
                            " or failed to get rebalance status")

        # Check the dir count after rebalance
        cmd = f'cd {self.mountpoint}/master; ls -l | wc -l'
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        dir_count_after = int(ret['msg'][0].strip())

        # Check if there is any data loss
        if dir_count_before != dir_count_after:
            raise Exception("There is data loss")
