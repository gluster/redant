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

Description: Tests to check that there is no data loss when
             remove-brick operation is stopped and then new bricks
             are added to the volume.
"""

# disruptive;dist-rep
# TODOdist,dist-rep,dist-disp,dist-arb
from time import sleep
from tests.d_parent_test import DParentTest


class TestRemoveBrickNoCommitFollowedByRebalance(DParentTest):
    def run_test(self, redant):
        """
         Steps :
         1) Create a volume.
         2) Mount the volume using FUSE.
         3) Create files and dirs on the mount-point.
         4) Calculate the arequal-checksum on the mount-point
         5) Start remove-brick operation on the volume.
         6) While migration is in progress, stop the remove-brick
            operation.
         7) Add-bricks to the volume and trigger rebalance.
         8) Wait for rebalance to complete.
         9) Calculate the arequal-checksum on the mount-point.
         """
        # Start IO on mounts
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        file_dir_script = "/usr/share/redant/script/file_dir_ops.py"
        cmd = (f"python3 {file_dir_script} create_deep_dirs_with_files"
               " --dir-length 2 --dir-depth 2 --max-num-of-dirs 2 "
               " --num-of-files 10 --file-type empty-file"
               f" {self.mountpoint}/")
        proc = redant.execute_command_async(cmd, self.client_list[0])

        # Validate deep dirs and files are created successfully
        if not redant.validate_io_procs(proc, self.mounts):
            raise Exception("IO failed on some of the clients")

        # Calculate arequal-checksum before starting remove-brick
        arequal_before = redant.collect_mounts_arequal(self.mounts)

        # Form bricks list for volume shrink
        remove_brick_list = (redant.form_bricks_list_to_remove_brick(
                             self.server_list[0], self.vol_name))
        if remove_brick_list is None:
            raise Exception(f"Volume {self.vol_name}: Failed to form bricks"
                            " list for shrink")

        # Shrink volume by removing bricks
        redant.remove_brick(self.server_list[0], self.vol_name,
                            remove_brick_list, "start")

        # Log remove-brick status
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  remove_brick_list, "status")
        # Check if migration is in progress
        if r'in progress' in ret:
            # Stop remove-brick process
            redant.remove_brick(self.server_list[0], self.vol_name,
                                remove_brick_list, "stop")
            redant.logger.info("Stopped remove-brick process successfully")
        else:
            redant.logger.error("Migration for remove-brick is complete")

        # Sleep for 30 secs so that any running remove-brick process stops
        sleep(30)

        # Add bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   distribute_count=3, force=True)
        if not ret:
            raise Exception("Failed to add-brick to the volume")

        # Tigger rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0])
        if not ret:
            raise Exception("Rebalace is not yet complete on the volume "
                            f"{self.vol_name}")

        # Calculate arequal-checksum on mount-point
        arequal_after = self.redant.collect_mounts_arequal(self.mounts)

        if arequal_before != arequal_after:
            raise Exception("There is data loss")
