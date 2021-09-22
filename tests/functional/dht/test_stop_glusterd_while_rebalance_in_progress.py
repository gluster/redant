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

Description:
    Rebalance should proceed even if glusterd is down on a node.
"""
# disruptive;dist,rep,disp,dist-rep,dist-disp

import traceback
import random
from time import sleep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """
        check if glusterd is started or not on the node
        """
        try:
            if self.is_glusterd_stop:
                self.redant.start_glusterd(self.random_server)

                # Waiting for glusterd to start completely
                ret = (self.redant.
                       wait_for_glusterd_to_start(self.random_server))
                if not ret:
                    raise Exception("Failed to start glusterd on node"
                                    f"{self.random_server}")

                # Validate all the peers are in connected state
                count = 0
                while count < 80:
                    ret = (self.redant.
                           validate_peers_are_connected(self.server_list,
                                                        self.server_list[0]))
                    if ret:
                        self.redant.logger.info("All peers are in connected "
                                                "state")
                        break
                    sleep(2)
                    count += 1

                if not ret:
                    raise Exception("All peers are not in connected state")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test Case:
        1) Setup and mount a volume on client.
        2) Start IO on mount points
        3) Expanding volume by adding bricks to the volume
        4) Start Rebalance
        5) Wait for at least one file to be lookedup/scanned on the nodes
        6) Stop glusterd on a random server
        7) Wait for rebalance to complete
        """
        # Start IO on mounts
        self.is_glusterd_stop = False
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        all_mounts_procs = []
        for index, mount_obj in enumerate(self.mounts, start=1):
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      index + 10, 3, 3, 3,
                                                      10, mount_obj['client'])
            all_mounts_procs.append(proc)

        # Wait for IO to complete
        if not redant.wait_for_io_to_complete(all_mounts_procs, self.mounts):
            raise Exception("Failed to wait for IO to complete")

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

        # Wait for at least one file to be lookedup/scanned on the nodes
        status_info = redant.get_rebalance_status(self.vol_name,
                                                  self.server_list[0])
        if status_info is None:
            raise Exception("Rebalance status command has returned None")

        count = 0
        while count < 100:
            lookups_start_count = 0
            for node in range(len(status_info['node'])):
                status_info = redant.get_rebalance_status(self.vol_name,
                                                          self.server_list[0])
                lookups_file_count = status_info['node'][node]['lookups']
                if int(lookups_file_count) > 0:
                    lookups_start_count += 1
                    sleep(5)
            if lookups_start_count == len(self.server_list):
                redant.logger.info(f"Volume {self.vol_name}: At least one "
                                   "file is lookedup/scanned "
                                   "on all nodes")
                break
            count += 1

        # Form a new list of servers without mnode in it to prevent mnode
        # from glusterd failure
        nodes = self.server_list[:]
        nodes.remove(self.server_list[0])

        # Stop glusterd on a server
        self.random_server = random.choice(nodes)
        redant.stop_glusterd(self.random_server)
        self.is_glusterd_stop = True

        # Wait for rebalance to complete
        ret = (redant.wait_for_rebalance_to_complete(self.vol_name,
                                                     self.server_list[0],
                                                     timeout=1800))
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")
