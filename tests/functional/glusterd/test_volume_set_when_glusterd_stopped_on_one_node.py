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

 Description:
    Volume set operation when glusterd is stopped on one node
"""

import traceback
from time import sleep
from random import choice
from tests.d_parent_test import DParentTest

# disruptive;dist,rep,dist-rep,disp,dist-disp


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway then wait for IO to comlete before
        calling the terminate function of DParentTest and also check if
        glusterd is started or not on the restarted node
        """
        try:
            self.redant.start_glusterd(self.random_server)

            # Waiting for glusterd to start completely
            ret = self.redant.wait_for_glusterd_to_start(self.random_server)
            if not ret:
                raise Exception("Failed to start glusterd on node"
                                f"{self.random_server}")

            ret = self.redant.wait_for_io_to_complete(self.list_of_procs,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test Case:
        1) Setup and mount a volume on client.
        2) Stop glusterd on a random server.
        3) Start IO on mount points
        4) Set an option on the volume
        5) Start glusterd on the stopped node.
        6) Verify all the bricks are online after starting glusterd.
        7) Check if the volume info is synced across the cluster.
        """
        # Fetching the bricks list and storing it for later use
        list1 = redant.get_online_bricks_list(self.vol_name,
                                              self.server_list[0])
        if list1 is None:
            raise Exception("Failed to get online brick list")

        # Fetching a random server from list.
        self.random_server = choice(self.server_list[1:])

        # Stopping glusterd on one node.
        redant.stop_glusterd(self.random_server)

        # Get mountpoint list
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # run IO on mountpoint
        self.list_of_procs = []
        self.counter = 1
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      self.counter,
                                                      2, 6, 3, 5,
                                                      mount_obj['client'])

            self.list_of_procs.append(proc)
            self.counter += 10

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # set a option on volume, stat-prefetch on
        self.options = {"stat-prefetch": "on"}
        redant.set_volume_options(self.vol_name, self.options,
                                  self.server_list[0])

        # start glusterd on the node where glusterd is stopped
        redant.start_glusterd(self.random_server)

        # Waiting for glusterd to start completely
        ret = redant.wait_for_glusterd_to_start(self.random_server)
        if not ret:
            raise Exception("Failed to start glusterd on node"
                            f"{self.random_server}")

        # Confirm if all the bricks are online or not
        count = 0
        while count < 10:
            list2 = redant.get_online_bricks_list(self.vol_name,
                                                  self.server_list[0])
            if list2 is None:
                raise Exception("Failed to get online brick list")
            if list1 == list2:
                break
            sleep(2)
            count += 1

        if list1 != list2:
            raise Exception("Unexpected: All the bricks in the"
                            "volume are not online")

        # volume info should be synced across the cluster
        vol_info1 = redant.get_volume_info(self.server_list[0], self.vol_name)
        if vol_info1 is None:
            raise Exception("Failed to get volume info from node"
                            f" {self.server_list[0]}")

        count = 0
        while count < 60:
            vol_info2 = redant.get_volume_info(self.random_server,
                                               self.vol_name)
            if vol_info2 is None:
                raise Exception("Failed to get volume info from node"
                                f" {self.random_server}")
            if vol_info1 == vol_info2:
                break
            sleep(2)
            count += 1

        if vol_info1 != vol_info2:
            raise Exception("Volume info is not synced in the"
                            "restarted node")
