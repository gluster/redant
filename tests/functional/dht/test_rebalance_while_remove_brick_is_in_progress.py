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
"""
# disruptive;dist,dist-rep,dist-disp

import traceback
from common.ops.gluster_ops.constants import (TEST_LAYOUT_IS_COMPLETE,
                                              FILETYPE_DIRS)
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    def terminate(self):
        """
        Stop remove brick operation, if the status is 'in-progress'
        """
        try:
            if self.remove_brick_list:
                status_info = (self.redant.get_remove_brick_status(
                               self.server_list[0], self.vol_name,
                               self.remove_brick_list))
                if 'in progress' in status_info['aggregate']['statusStr']:
                    # Shrink volume by removing bricks with option start
                    self.redant.remove_brick(self.server_list[0],
                                             self.vol_name,
                                             self.remove_brick_list, "stop")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        - Create directories and files on the mount point.
        -  now remove one of the brick from the volume
            gluster volume remove-brick <vol> <brick> start
        - immediately start rebalance on the same volume
            gluster volume rebalance <vol> start
        """
        self.remove_brick_list = []
        # Start IO on mounts
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        all_mounts_procs = []
        for index, mount_obj in enumerate(self.mounts, start=1):
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      index + 10, 2, 15, 5,
                                                      5, mount_obj['client'])
            all_mounts_procs.append(proc)

        # Wait for IO to complete
        if not redant.wait_for_io_to_complete(all_mounts_procs, self.mounts):
            raise Exception("Failed to wait for IO to complete")

        # List all files and dirs created
        if not redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to find list and dirs opn mountpoints")

        # DHT Layout validation
        for mount_obj in self.mounts:
            ret = (redant.validate_files_in_dir(mount_obj['client'],
                   mount_obj['mountpath'], test_type=TEST_LAYOUT_IS_COMPLETE,
                   file_type=FILETYPE_DIRS))
            if not ret:
                raise Exception("LAYOUT_IS_COMPLETE: FAILED")

        # Log Volume Info and Status before shrinking the volume.
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Form bricks list for Shrinking volume
        self.remove_brick_list = (redant.form_bricks_list_to_remove_brick(
                                  self.server_list[0], self.vol_name,
                                  subvol_num=1))

        if self.remove_brick_list is None:
            raise Exception("Failed to form bricks list to remove-brick. "
                            f"Hence unable to shrink volume {self.vol_name}")

        # Shrink volume
        redant.remove_brick(self.server_list[0], self.vol_name,
                            self.remove_brick_list, "start")

        # Log remove-brick status
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  self.remove_brick_list, "status")

        # Start rebalance while volume shrink in-progress
        ret = redant.rebalance_start(self.vol_name, self.server_list[0],
                                     False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected:Rebalance started successfully"
                            " while volume shrink is in-progress")
