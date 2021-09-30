"""
 Copyright (C) 2017-2020 Red Hat, Inc. <http://www.redhat.com>

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
    TC to do rebalance from multiple clients, when IO in progress
"""

# disruptive;dist,rep,disp,dist-rep,dist-disp
from common.ops.gluster_ops.constants import (FILETYPE_DIRS,
                                              TEST_LAYOUT_IS_COMPLETE)
import traceback
from tests.d_parent_test import DParentTest


class TestRebalanceValidation(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not self.redant.wait_for_io_to_complete(self.io_process,
                                                           self.mounts):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        - Create and start a volume
        - Mount the volume on clients and start IO
        - Expand volume while IO is in progress
        - Start rebalance and wait for it to complete
        - Validate IO
        - Vaidate the LAYOUT
        - Check if there are any failures in rebalance
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.io_process = []
        self.is_io_running = False
        index = 0

        for index, mount_obj in enumerate(self.mounts, start=1):
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      index + 10, 2, 5, 5, 5,
                                                      mount_obj['client'])
            self.io_process.append(proc)
            self.is_io_running = True

        # Log Volume Info and Status before expanding the volume.
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Expanding volume by adding bricks to the volume when IO in progress
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to expand the volume {self.vol_name}")

        # Wait for gluster processes to come online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Log Volume Info and Status after expanding the volume
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=1800)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Check Rebalance status after rebalance is complete
        redant.get_rebalance_status(self.vol_name, self.server_list[0])

        # Validate IO
        ret = redant.validate_io_procs(self.io_process, self.mounts)
        if not ret:
            raise Exception("Failed to validate IO")
        self.is_io_running = False

        # List all files and dirs created
        ret = redant.list_all_files_and_dirs_mounts(self.mounts)
        if not ret:
            raise Exception("Failed to list files and dirs")

        # DHT Layout validation
        ret = (redant.validate_files_in_dir(self.client_list[0],
               self.mountpoint, test_type=TEST_LAYOUT_IS_COMPLETE,
               file_type=FILETYPE_DIRS))
        if not ret:
            raise Exception("LAYOUT_IS_COMPLETE: FAILED")

        # Checking if there are any migration failures
        status = redant.get_rebalance_status(self.vol_name,
                                             self.server_list[0])
        if int(status['aggregate']['failures']) > 0:
            raise Exception("Rebalance failed to migrate few files")
