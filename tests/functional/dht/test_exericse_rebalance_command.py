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
"""
# disruptive;rep,dist,dist-rep,disp,dist-disp

from time import sleep
from tests.d_parent_test import DParentTest


class TestExerciseRebalanceCommand(DParentTest):

    def _test_fix_layout_start(self):
        # Start IO on mounts
        self.all_mounts_procs = []
        index = 1
        for mount_obj in self.mounts:
            proc = (self.
                    redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                       index + 10,
                                                       2, 2, 2, 10,
                                                       mount_obj['client']))

            self.all_mounts_procs.append(proc)

        # Wait for IO to complete
        ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                  self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # List all files and dirs created
        if not self.redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to find list and dirs opn mountpoints")

        # Get arequal checksum before starting fix-layout
        arequal_before = self.redant.collect_mounts_arequal(self.mounts)

        # Log Volume Info and Status before expanding the volume.
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Form brick list for expanding volume
        add_brick_list = (self.redant.form_brick_cmd_to_add_brick(
                          self.server_list[0], self.vol_name,
                          self.server_list, self.brick_roots,
                          distribute_count=1))
        if not add_brick_list:
            raise Exception("Failed to form add-brick cmd")

        # Expanding volume by adding bricks to the volume
        self.redant.add_brick(self.vol_name, add_brick_list,
                              self.server_list[0], force=True)

        # Wait for gluster processes to come online
        if not (self.redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")

        # Log Volume Info and Status after expanding the volume
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Verify volume's all process are online
        if not (self.redant.verify_all_process_of_volume_are_online(
                self.vol_name, self.server_list[0])):
            raise Exception("All process are not online")

        # Start Rebalance fix-layout
        self.redant.rebalance_start(self.vol_name, self.server_list[0],
                                    fix_layout=True)

        # Wait for fix-layout to complete
        ret = self.redant.wait_for_fix_layout_to_complete(self.server_list[0],
                                                          self.vol_name)
        if not ret:
            raise Exception(f"Volume {self.vol_name}: Fix-layout is either "
                            "failed or in-progress")

        # Check Rebalance status after fix-layout is complete
        self.redant.get_rebalance_status(self.vol_name, self.server_list[0])

        # Get arequal checksum after fix-layout is complete
        arequal_after = self.redant.collect_mounts_arequal(self.mounts)

        # Compare arequals checksum before and after fix-layout
        if arequal_before != arequal_after:
            raise Exception("arequal checksum is NOT MATCHNG")

        # Check if there are any file migrations after fix-layout
        status_info = (self.redant.get_rebalance_status(self.vol_name,
                       self.server_list[0]))
        for node in range(len(status_info['node'])):
            status_info = (self.redant.get_rebalance_status(self.vol_name,
                           self.server_list[0]))
            file_migration_count = status_info['node'][node]['files']
            if int(file_migration_count) != 0:
                raise Exception("Few files are migrated")

        # Check if new bricks contains any files
        add_brick_list = add_brick_list.split(" ")
        for brick in add_brick_list:
            brick_node, brick_path = brick.split(":")
            cmd = ('find %s -type f ! -perm 1000 | grep -ve .glusterfs'
                   % brick_path)
            ret = self.redant.execute_abstract_op_node(cmd, brick_node, False)
            out = ret['msg']
            if len(out) != 0:
                raise Exception("Files(excluded linkto files) are present on "
                                f"{brick_node}:{brick_path}")

    def _test_rebalance_start_status_stop(self):
        # Form brick list for expanding volume
        add_brick_list = (self.redant.form_brick_cmd_to_add_brick(
                          self.server_list[0], self.vol_name,
                          self.server_list, self.brick_roots,
                          distribute_count=1))
        if not add_brick_list:
            raise Exception("Failed to form add-brick cmd")

        # Expanding volume by adding bricks to the volume
        self.redant.add_brick(self.vol_name, add_brick_list,
                              self.server_list[0], force=True)

        # Wait for gluster processes to come online
        if not (self.redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")

        # Log Volume Info and Status after expanding the volume
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Verify volume's all process are online
        if not (self.redant.verify_all_process_of_volume_are_online(
                self.vol_name, self.server_list[0])):
            raise Exception("All process are not online")

        # Getting arequal checksum before rebalance start
        arequal_before = self.redant.collect_mounts_arequal(self.mounts)

        # Start Rebalance
        self.redant.rebalance_start(self.vol_name, self.server_list[0])

        # Stop on-going rebalance
        self.redant.rebalance_stop(self.vol_name, self.server_list[0])

        # Wait till the on-going file migration completes on all servers
        count = 0
        while count < 80:
            rebalance_count = 0
            for server in self.server_list:
                ret = self.redant.execute_abstract_op_node("pgrep rebalance",
                                                           server, False)
                if ret['error_code'] == 0:
                    rebalance_count += 1
            if rebalance_count == len(self.server_list):
                break
            sleep(2)
            count += 1

        # List all files and dirs from mount point
        if not self.redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to find list and dirs opn mountpoints")

        # Getting arequal checksum after the rebalance is stopped
        arequal_after = self.redant.collect_mounts_arequal(self.mounts)

        # Comparing arequals checksum before start of rebalance and
        # after the rebalance is stopped
        if arequal_before != arequal_after:
            raise Exception("arequal checksum is NOT MATCHNG")

    def _test_rebalance_with_force(self):

        # Getting arequal checksum before rebalance
        arequal_before = self.redant.collect_mounts_arequal(self.mounts)

        # Log Volume Info and Status before expanding the volume.
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Expanding volume by adding bricks to the volume
        ret = self.redant.expand_volume(self.server_list[0], self.vol_name,
                                        self.server_list, self.brick_roots,
                                        force=True)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Wait for gluster processes to come online
        if not (self.redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")

        # Verify volume's all process are online
        if not (self.redant.verify_all_process_of_volume_are_online(
                self.vol_name, self.server_list[0])):
            raise Exception("All process are not online")

        # Log Volume Info and Status after expanding the volume
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Start Rebalance with force
        self.redant.rebalance_start(self.vol_name, self.server_list[0],
                                    force=True)

        # Wait for rebalance to complete
        ret = (self.redant.wait_for_rebalance_to_complete(self.vol_name,
               self.server_list[0], timeout=600))
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Getting arequal checksum after rebalance
        arequal_after = self.redant.collect_mounts_arequal(self.mounts)

        # Comparing arequals checksum before and after rebalance with force
        # option
        if arequal_before != arequal_after:
            raise Exception("arequal checksum is NOT MATCHNG")

        # Checking if rebalance skipped any files
        status = (self.redant.get_rebalance_status(self.vol_name,
                  self.server_list[0]))
        for each_node in status['node']:
            if int(each_node['skipped']) != 0:
                raise Exception("Few files are skipped on node"
                                f" {each_node['nodeName']}")

    def run_test(self, redant):
        """
        Steps:
        1) Create a gluster volume and start it.
        2) create some data on the mount point.
        3) Calculate arequal checksum on the mount point.
        4) Add few bricks to the volume.
        5) Initiate rebalance using command
            gluster volume rebalance <vol> start
        6) Check the status of the rebalance using command,
            gluster volume rebalance <vol> status
        7) While migration in progress stop the rebalance in the mid
            gluster volume rebalance <vol> stop.
        8) check whether migration is stopped or not.
        9) once rebalance stops , calculate the checksum on the mount point.
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self._test_fix_layout_start()
        self._test_rebalance_start_status_stop()
        self._test_rebalance_with_force()
