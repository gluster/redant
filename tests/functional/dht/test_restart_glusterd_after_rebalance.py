"""
  Copyright (C) 2018-2020 Red Hat, Inc. <http://www.redhat.com>

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

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test Case:
        1) Setup and mount a volume on client.
        2) Start IO on mount points
        3) Expanding volume by adding bricks to the volume
        4) Start Rebalance and wait for it to complete
        5) restart glusterd on all servers
        6) Check if rebalance process has started or not
           after glusterd restart.
        """

        # Start IO on mounts
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        index = 1
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      index,
                                                      2, 2, 1, 2,
                                                      mount_obj['client'])

            self.all_mounts_procs.append(proc)
            index += 10

        # Wait for IO to complete
        ret = redant.wait_for_io_to_complete(self.all_mounts_procs,
                                             self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # List all files and dirs created
        if not redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to find list and dirs opn mountpoints")

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

        # restart glusterd on all servers
        redant.restart_glusterd(self.server_list)

        # Check if glusterd is running on all servers(expected: active)
        ret = redant.is_glusterd_running(self.server_list)
        if ret != 1:
            raise Exception("glusterd is not running")

        # Check if rebalance process has started after glusterd restart
        for server in self.server_list:
            ret = redant.execute_abstract_op_node("pgrep rebalance", server,
                                                  False)
            if ret['error_code'] == 0:
                raise Exception("Rebalance process is triggered on "
                                f"{server} after glusterd restart")
