"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test case validates remove-brick and rebalance in a dispersed
    volume
"""

# disruptive;dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestDispersedWithAddBrick(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete if the TC fails early
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
        - Write IO's
        - Start remove brick
        - Validate IOs
        - Start rebalance
        - Wait for rebalance to complete
        - Start IO's and Vaildate IO's
        """
        # Write IO
        self.is_io_running = False
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        count = 1
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 10, 5, 5,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count = count + 10
        self.is_io_running = True

        # Start remove-brick (subvolume-decrease)
        ret = redant.shrink_volume(self.server_list[0], self.vol_name)
        if not ret:
            raise Exception("Failed to remove bricks")

        # Log Volume Info and Status after shrinking the volume
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")

        # Validating IO's and waiting to complete
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on the mounts")
        self.is_io_running = False

        # Start IO on all mounts after rebalance completes
        self.all_mounts_procs = []
        count = 100
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 10, 5, 5,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count = count + 10

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on the mounts")
