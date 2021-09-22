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

 You should have received a copy of the GNU General Public License along`
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    TC to check rebalance after add-brick with rsync in progress
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
from copy import deepcopy
import traceback
from tests.d_parent_test import DParentTest


class TestAddBrickRebalanceWithRsyncInProgress(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 3
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.list_of_io_processes, self.mounts)):
                    raise Exception("Failed ot wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Create, start and mount a volume.
        2. Create a directory on the mount point and start IO.
        3. Create another directory on the mount point and start rsync of
           the IO directory.
        4. Add bricks to the volume
        5. Trigger rebalance on the volume.
        6. Wait for rebalance to complete on volume.
        7. Wait for I/O to complete.
        8. Validate if checksum of both the untar and rsync is same.
        """
        self.is_io_running = False
        # List of I/O processes
        self.list_of_io_processes = []

        # Create a dir to start untar
        self.io_dir = f"{self.mountpoint}/io_dir"
        redant.create_dir(self.mountpoint, "io_dir", self.client_list[0])

        # Start IO on the directory created under mountpoint
        proc = redant.create_deep_dirs_with_files(f"{self.mountpoint}/io_dir",
                                                  1, 3, 4, 4, 20,
                                                  self.client_list[0])
        self.list_of_io_processes.append(proc)
        self.mounts = [{
            "client": self.client_list[0],
            "mountpath": self.io_dir
        }]
        self.is_io_running = True

        # Create a new directory and start rsync
        self.rsync_dir = f"{self.mountpoint}/rsyncdir"
        redant.create_dir(self.mountpoint, "rsyncdir", self.client_list[0])

        # Start rsync for the directory on mount point
        cmd = f"rsync -azr {self.io_dir} {self.rsync_dir}"
        proc = redant.execute_command_async(cmd, self.client_list[0])
        self.list_of_io_processes.append(proc)
        self.mounts.append({
            "client": self.client_list[0],
            "mountpath": self.rsync_dir
        })

        # Add bricks to the volume
        force = False
        if self.volume_type == "dist-disp":
            force = True
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=force)
        if not ret:
            raise Exception("Failed to add brick with rsync on volume "
                            f"{self.vol_name}")

        # Trigger rebalance on the volume
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=6000)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Wait for IO to complete.
        ret = redant.validate_io_procs(self.list_of_io_processes, self.mounts)
        if not ret:
            raise Exception("IO didn't complete or failed on client")
        self.is_io_running = False

        # As we are running rsync and untar together, there are situations
        # when some of the new files created by IO is not synced
        # through rsync which causes checksum to retrun different value,
        # Hence to take care of this corner case we are rerunning rsync.
        cmd = f"rsync -azr {self.io_dir} {self.rsync_dir}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check data consistency on both the directories
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        rsync_checksum = (redant.collect_mounts_arequal(self.mounts,
                          'rsyncdir/io_dir/'))

        untar_checksum = redant.collect_mounts_arequal(self.mounts,
                                                       'io_dir')
        if rsync_checksum != untar_checksum:
            raise Exception("Checksum on untar dir and checksum on rsync"
                            " dir didn't match")
