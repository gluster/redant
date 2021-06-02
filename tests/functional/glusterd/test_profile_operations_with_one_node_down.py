"""
Copyright (C) 2019-2020  Red Hat, Inc. <http://www.redhat.com>

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
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Test Description:
Tests to check basic profile operations with one node down.
"""
# disruptive;dist-rep,disp,dist-disp
import traceback
from random import randint
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """
        This function will start the glusterd
        on the random server chosen and check
        if all peers are connected
        """
        # Starting glusterd on node where stopped.
        try:
            self.redant.start_glusterd(self.server)
            self.redant.wait_for_glusterd_to_start(self.server)
            # Checking if peer is connected
            for ser in self.server_list[1:]:
                self.redant.wait_for_peers_to_connect(self.server_list[0],
                                                      ser)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):

        """
        Test Case:
        1) Create a volume and start it.
        2) Mount volume on client and start IO.
        3) Start profile info on the volume.
        4) Stop glusterd on one node.
        5) Run profile info with different parameters
           and see if all bricks are present or not.
        6) Stop profile on the volume.
        """

        # Start IO on mount points.
        redant.logger.info("Starting IO on all mounts...")
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.list_of_procs = []
        self.counter = 1
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      self.counter,
                                                      4, 6, 3, 5,
                                                      mount_obj['client'])

            self.list_of_procs.append(proc)
            self.counter += 10

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # Start profile on volume.
        redant.profile_start(self.vol_name, self.server_list[0])

        # Fetching a random server from list.
        self.random_server = randint(1, len(self.server_list)-1)
        self.server = self.server_list[self.random_server]

        # Stopping glusterd on one node.
        redant.stop_glusterd(self.server)

        if not redant.wait_for_glusterd_to_stop(self.server):
            raise Exception(f"Error: Glusterd is still running on "
                            f"{self.server}\n")
        # Getting and checking output of profile info.
        ret = redant.profile_info(self.vol_name,
                                  self.server_list[0])
        out = " ".join(ret['msg'])

        # Checking if all bricks are present in profile info.
        brick_list = redant.get_online_bricks_list(self.vol_name,
                                                   self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get the online bricks list")
        for brick in brick_list:
            if brick not in out:
                raise Exception(f"Brick {brick} not a part of profile"
                                f" info output")

        # Running profile info with different profile options.
        profile_options = ['peek', 'incremental', 'clear', 'incremental peek',
                           'cumulative']
        for option in profile_options:

            # Getting and checking output of profile info.
            ret = redant.profile_info(self.vol_name,
                                      self.server_list[0],
                                      option)
            out = " ".join(ret['msg'])

            # Checking if all bricks are present in profile info peek.
            for brick in brick_list:
                if brick not in out:
                    raise Exception(f"Brick {brick} not a part of profile"
                                    f" info {option} output")

        # Starting glusterd on node where stopped.
        redant.start_glusterd(self.server)
        if not redant.wait_for_glusterd_to_start(self.server):
            raise Exception(f"Error: Glusterd is not running on "
                            f"{self.server}\n")

        # Checking if peer is connected
        for ser in self.server_list[1:]:
            self.redant.wait_for_peers_to_connect(self.server_list[0],
                                                  ser)
        # Stop profile on volume.
        redant.profile_stop(self.vol_name,
                            self.server_list[0])
