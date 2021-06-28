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
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Description:
TC to check profile operations simultaneously on different nodes
"""

from time import sleep
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
            self.redant.cleanup_volume(self.volume_name1, self.server_list[0])
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
        3) Start profile on the volume.
        4) Create another volume.
        5) Start profile on the volume.
        6) Run volume status in a loop in one of the node.
        7) Run profile info for the new volume on one of the other node
        8) Run profile info for the new volume in loop for 100 times on
           the other node
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

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # Create and start a volume
        volume_type1 = 'dist'
        self.volume_name1 = f"{self.test_name}-{volume_type1}-1"
        redant.setup_volume(self.volume_name1, self.server_list[0],
                            self.vol_type_inf[self.conv_dict[volume_type1]],
                            self.server_list, self.brick_roots)

        # Start profile on volume.
        redant.profile_start(self.volume_name1, self.server_list[0])

        # Run volume status on one of the node in loop
        cmd = "for i in `seq 1 100`;do gluster v status;done"
        proc1 = redant.execute_command_async(cmd, self.server_list[1])

        # Check profile on one of the other node
        cmd = f"gluster v profile {self.volume_name1} info"
        count = 0
        while count < 20:
            ret = redant.execute_abstract_op_node(cmd, self.server_list[0],
                                                  False)
            if ret['error_code'] == 0:
                break
            sleep(2)
            count += 1

        if ret['error_code'] != 0:
            raise Exception(f"Failed to get profile for volume "
                            f"{self.volume_name1}.Error: {ret['error_msg']}")

        # Run volume profile info on one of the other node in loop
        cmd = (f"for i in `seq 1 100`;do gluster v profile "
               f"{self.volume_name1} info;done")
        proc2 = redant.execute_command_async(cmd, self.server_list[2])

        ret = redant.wait_till_async_command_ends(proc1)
        if ret['error_code'] != 0:
            raise Exception(f"Failed to run volume status in a loop"
                            f" on node {self.server_list[1]}")

        ret = redant.wait_till_async_command_ends(proc2)
        if ret['error_code'] != 0:
            raise Exception(f"Failed to run profile info in a loop"
                            f" on node {self.server_list[2]}")

        # Checking for core files.
        ret = redant.check_core_file_exists(self.server_list, test_timestamp)
        if ret:
            raise Exception("glusterd service should not have crashed")

        # Checking whether glusterd is running or not
        ret = redant.is_glusterd_running(self.server_list)
        if ret != 1:
            raise Exception("Glusterd not running on servers")
