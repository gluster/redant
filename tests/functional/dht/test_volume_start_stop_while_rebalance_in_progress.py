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
    This testcase verifies, volume stop should not be allowed while
    rebalance is in-progress and it should throw appropriate error.
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp

from common.ops.gluster_ops.constants import \
    (FILETYPE_DIRS, FILETYPE_FILES, TEST_FILE_EXISTS_ON_HASHED_BRICKS)

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):

        # The --dir-length argument value for
        # file_dir_ops.py create_deep_dirs_with_files is set to 10
        # (refer to the cmd in setUp method). This means every mount will
        # create
        # 10 top level dirs. For every mountpoint/testcase to create new set of
        # dirs, we are incrementing the counter by --dir-length value i.e 10
        # in this test suite.
        #
        # If we are changing the --dir-length to new value, ensure the counter
        # is also incremented by same value to create new set of files/dirs.

        # Start IO on mounts
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        count = 1
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 1, 2, 2, 55,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count = count + 10

        # Wait for IO to complete
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # List all files and dirs created
        if not (redant.
                list_all_files_and_dirs_mounts(self.mounts)):
            raise Exception("Failed to list files and dirs")

        # DHT Layout and hash validation
        for mount_obj in self.mounts:
            ret = (redant.validate_files_in_dir(mount_obj['client'],
                   mount_obj['mountpath'],
                   test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS,
                   file_type=FILETYPE_FILES | FILETYPE_DIRS))
            if not ret:
                raise Exception("Hash Layout Values: Fail")

        # Log Volume Info and Status before expanding the volume.
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Expanding volume by adding bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=True)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

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

        # Wait for gluster processes to come online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(
                self.vol_name, self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Logging rebalance status
        ret = redant.get_rebalance_status(self.vol_name,
                                          self.server_list[0])
        if ret is None:
            raise Exception("Rebalance status command has returned None")
        status = ret['aggregate']['statusStr']
        if 'in progress' not in status:
            raise Exception("Rebalance process is not running")

        # Try to stop the volume
        ret = redant.volume_stop(self.vol_name, self.server_list[0],
                                 excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Expected: It should fail to stop "
                            "volume when rebalance is in progress. "
                            "Actual: Successfully "
                            f"stopped volume {self.vol_name}")

        # Check volume info to check the status of volume
        volinfo = redant.get_volume_info(self.server_list[0], self.vol_name)
        if not volinfo:
            raise Exception("Failed to get vol info")
        if volinfo[self.vol_name]['statusStr'] != 'Started':
            raise Exception("Volume state is \"Stopped\"")
