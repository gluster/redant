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

# disruptive;dist,rep,disp,dist-rep,dist-disp

import traceback
from common.ops.gluster_ops.constants import (FILETYPE_DIRS,
                                              TEST_LAYOUT_IS_COMPLETE)
from tests.d_parent_test import DParentTest


class RebalanceValidation(DParentTest):

    def terminate(self):
        """
        Wait for rebalance to stop
        """
        try:
            status_info = (self.
                           redant.get_rebalance_status(self.vol_name,
                                                       self.server_list[0]))
            status = status_info['aggregate']['statusStr']
            if 'in progress' in status:
                # Stop rebalance on the volume
                ret = self.redant.rebalance_stop(self.vol_name,
                                                 self.server_list[0])
                if ret['msg']['opRet'] != '0':
                    raise Exception("Rebalance stop failed")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        # Start IO on mounts
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        for index, mount_obj in enumerate(self.mounts, start=1):
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      index + 10, 2, 5, 5,
                                                      10, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Wait for IO to complete
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # List all files and dirs created
        if not redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to find list and dirs opn mountpoints")

        # DHT Layout validation
        ret = (redant.validate_files_in_dir(self.client_list[0],
               self.mountpoint, test_type=TEST_LAYOUT_IS_COMPLETE,
               file_type=FILETYPE_DIRS))
        if not ret:
            raise Exception("LAYOUT_IS_COMPLETE: FAILED")

        # Log Volume Info and Status before expanding the volume.
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Expanding volume by adding bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=True)
        if not ret:
            raise Exception(f"Failed to expand the volume {self.vol_name}")

        # Wait for gluster processes to come online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Log Volume Info and Status after expanding the volume
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Check if rebalance is running
        status_info = redant.get_rebalance_status(self.vol_name,
                                                  self.server_list[0])
        status = status_info['aggregate']['statusStr']
        if 'in progress' in status:
            # Form bricks list for Shrinking volume
            self.remove_brick_list = (redant.form_bricks_list_to_remove_brick(
                                      self.server_list[0], self.vol_name,
                                      subvol_num=1))
            if self.remove_brick_list is None:
                raise Exception("Failed to form bricks list for shrink")

            # Shrinking volume by removing bricks
            ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                      self.remove_brick_list, "start",
                                      excep=False)
            if ret['msg']['opRet'] == '0':
                raise Exception("Successfully removed bricks while volume "
                                "rebalance is in-progress. "
                                "Expected:Failed to start remove-brick as "
                                "rebalance is in-progress")
        else:
            raise Exception("Rebalance process is not running")
