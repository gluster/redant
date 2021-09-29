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
51 Franklin Street, Fifth Floor, Boston, MA 02110-131 USA.

Description:
    Rebalance with hidden files
"""

# disruptive;dist,disp,rep,dist-rep,dist-disp

from common.ops.gluster_ops.constants import \
    (FILETYPE_FILES, TEST_FILE_EXISTS_ON_HASHED_BRICKS)
from tests.d_parent_test import DParentTest


class TestRebalanceWithSpecialFiles(DParentTest):

    def run_test(self, redant):
        """
        Rebalance with hidden files
        - Create Volume and start it.
        - Create some hidden files on mount point.
        - Once it is complete, start some IO.
        - Add brick into the volume and start rebalance
        - All IO should be successful.
        """
        # Start IO on mounts
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        counter = 1
        for mount_obj in self.mounts:
            proc = redant.create_files("1k", mount_obj['mountpath'],
                                       mount_obj['client'], 99,
                                       f'.file{counter}')
            counter += 100
        self.all_mounts_procs.append(proc)

        # validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # List all files and dirs created
        if not redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to find list and dirs opn mountpoints")

        # Verify DHT values across mount points
        for mount_obj in self.mounts:
            ret = (redant.validate_files_in_dir(
                   mount_obj['client'], mount_obj['mountpath'],
                   test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS,
                   file_type=FILETYPE_FILES))
            if not ret:
                raise Exception("Files not created on correct sub-vols")

        # Getting areequal checksum before rebalance
        arequal_before_rebalance = redant.collect_mounts_arequal(self.mounts)

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
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Wait for gluster processes to come online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")

        # Verify volume's all process are online
        if not redant.wait_for_volume_process_to_be_online(self.vol_name,
                                                           self.server_list[0],
                                                           self.server_list):
            raise Exception(f"Failed to wait for volume {self.vol_name} "
                            "processes to be online")

        # Log Volume Info and Status after expanding the volume
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")
        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = (redant.wait_for_rebalance_to_complete(self.vol_name,
                                                     self.server_list[0],
                                                     timeout=1800))
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Checking if there are any migration failures
        status = redant.get_rebalance_status(self.vol_name,
                                             self.server_list[0])
        for each_node in status['node']:
            failed_files_count = int(each_node['failures'])
            if failed_files_count != 0:
                raise Exception("Rebalance failed to migrate few files on"
                                f"{each_node['nodeName']}")

        # Getting areequal checksum after rebalance
        arequal_after_rebalance = redant.collect_mounts_arequal(self.mounts)

        # Comparing arequals checksum before and after rebalance
        if arequal_before_rebalance != arequal_after_rebalance:
            raise Exception("arequal checksum is NOT MATCHNG")
