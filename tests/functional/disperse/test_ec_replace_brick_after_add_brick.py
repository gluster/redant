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
    TC to check replace-brick on ec volume after add-brick while IO in
    progress
"""

# disruptive;disp
import traceback
from random import choice
from tests.d_parent_test import DParentTest


class TestEcReplaceBrickAfterAddBrick(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mounts)):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test Steps:
        1. Create a pure-ec volume (say 1x(4+2))
        2. Mount volume on two clients
        3. Create some files and dirs from both mnts
        4. Add bricks in this case the (4+2) ie 6 bricks
        5. Create a new dir(common_dir) and in that directory create a distinct
           directory(using hostname as dirname) for each client and pump IOs
           from the clients(dd)
        6. While IOs are in progress replace any of the bricks
        7. Check for errors if any collected after step 6
        """
        self.is_io_running = False
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not all_bricks:
            raise Exception("Unable to get the bricks list")

        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for count, mount_obj in enumerate(self.mounts):
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 3, 5, 5, 5,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)

        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on the mounts")

        # Expand the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception("Expanding volume failed")

        # Create a new dir(common_dir) on mountpoint
        redant.create_dir(self.mountpoint, "common_dir", self.client_list[0])

        # Create distinct directory for each client under common_dir
        for each_client in self.client_list:
            redant.create_dir(f"{self.mountpoint}/common_dir", "$HOSTNAME",
                              each_client)

        # Run dd in the background and stdout,stderr to error.txt for
        # validating any errors after io completion.
        run_dd_cmd = (f"cd {self.mountpoint}/common_dir/$HOSTNAME; "
                      "for i in `seq 1 1000`; do dd if=/dev/urandom "
                      "of=file$i bs=4096 count=10 &>> error.txt; done")
        self.all_mounts_procs = []
        for each_client in self.mounts:
            proc = redant.execute_command_async(run_dd_cmd,
                                                each_client['client'])
            self.all_mounts_procs.append(proc)
        self.is_io_running = True

        # Get random brick from the bricks
        brick_to_replace = choice(all_bricks)
        node_from_brick_replace, _ = brick_to_replace.split(":")

        # Replace brick from the same node
        ret = redant.replace_brick_from_volume(self.vol_name,
                                               self.server_list[0],
                                               node_from_brick_replace,
                                               src_brick=brick_to_replace,
                                               brick_roots=self.brick_roots)
        if not ret:
            raise Exception("Replace brick failed")

        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on the mounts")
        self.is_io_running = False

        err_msg = "Too many levels of symbolic links"
        dd_log_file = f"{self.mountpoint}/common_dir/$HOSTNAME/error.txt"
        for each_client in self.mounts:
            ret = redant.occurences_of_pattern_in_file(each_client['client'],
                                                       err_msg, dd_log_file)
            if ret != 0:
                raise Exception(f"Either file {dd_log_file} doesn't exist or"
                                f" '{err_msg}' messages seen while replace "
                                "brick operation in-progress")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")
