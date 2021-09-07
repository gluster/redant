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
    Tests to check basic profile operations and profile info
    without having profile started
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;dist,rep,dist-rep,disp,dist-disp


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway, then the IO must be completed and
        the volumes created in the TC should be cleaned up and then the
        terminate function in the DParentTest is called
        """
        try:
            self.redant.cleanup_volume(self.server_list, self.volume_name1)
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
        1) Create a volume and start it.
        2) Mount volume on client and start IO.
        3) Start profile info on the volume.
        4) Run profile info with different parameters
           and see if all bricks are present or not.
        5) Stop profile on the volume.
        6) Create another volume.
        7) Start profile without starting the volume.
        """

        # Timestamp of current test case of start time
        ret = redant.execute_abstract_op_node('date +%s', self.server_list[0])
        test_timestamp = ret['msg'][0].rstrip('\n')

        # Get mountpoint list
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # run IO on mountpoint
        self.list_of_procs = []
        counter = 1
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      counter, 2, 5, 3, 5,
                                                      mount_obj['client'])

            self.list_of_procs.append(proc)
            counter += 10

        # Start profile on volume.
        redant.profile_start(self.vol_name, self.server_list[0])

        # Getting and checking output of profile info.
        ret = redant.profile_info(self.vol_name, self.server_list[0])
        output = " ".join(ret['msg'])

        # Checking if all bricks are present in profile info.
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get brick list from volume")
        else:
            for brick in brick_list:
                if brick not in output:
                    raise Exception(f"Brick {brick} not a part of profile"
                                    f" info output.")

        # Running profile info with different profile options.
        profile_options = ['peek', 'incremental', 'clear',
                           'incremental peek', 'cumulative']

        for option in profile_options:
            # Getting and checking output of profile info.
            redant.profile_info(self.vol_name, self.server_list[0],
                                option)
            output = " ".join(ret['msg'])

            # Checking if all bricks are present in profile info peek.
            for brick in brick_list:
                if brick not in output:
                    raise Exception(f"Brick {brick} not a part of profile"
                                    f" info output.")

        # Stop profile on volume.
        redant.profile_stop(self.vol_name, self.server_list[0])

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # Create and start a volume
        volume_type1 = 'dist'
        self.volume_name1 = f"{self.test_name}-{volume_type1}-1"
        redant.setup_volume(self.volume_name1, self.server_list[0],
                            self.vol_type_inf[volume_type1],
                            self.server_list, self.brick_roots)

        # Stop volume
        redant.volume_stop(self.volume_name1, self.server_list[0])

        # Start profile on volume.
        redant.profile_start(self.volume_name1, self.server_list[0])

        # Start volume
        redant.volume_start(self.volume_name1, self.server_list[0])

        # Merged the TC
        # test_profile_info_without_having_profile_started

        # Stopping profile for new TC
        redant.profile_stop(self.volume_name1, self.server_list[0])

        # Check profile info on volume without starting profile
        ret = redant.profile_info(self.volume_name1, self.server_list[0],
                                  '', False)
        if ret['error_code'] == 0:
            raise Exception(f"Unexpected:Successfully ran profile info"
                            f" on volume: {self.volume_name1}")

        # Running profile info with different profile options.
        profile_options = ['peek', 'incremental', 'clear',
                           'incremental peek', 'cumulative']

        for option in profile_options:
            # Getting and checking output of profile info.
            redant.profile_info(self.vol_name, self.server_list[0],
                                option, False)
            if ret['error_code'] == 0:
                raise Exception(f"Unexpected:Successfully ran profile info"
                                f" {option} on volume: {self.volume_name1}")

        # Checking for core files.
        ret = redant.check_core_file_exists(self.server_list, test_timestamp)
        if ret:
            raise Exception("glusterd service should not have crashed")

        # Checking whether glusterd is running or not
        ret = redant.is_glusterd_running(self.server_list)
        if ret != 1:
            raise Exception("Glusterd not running on servers")
