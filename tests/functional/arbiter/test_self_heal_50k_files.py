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
    TC to check self-heal with 50k files
"""

# disruptive;arb,dist-arb
from tests.d_parent_test import DParentTest


class TestSelfHeal50kFiles(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - Select bricks to bring offline
        - Bring brick offline
        - Create 50k files
        - Validate IO
        - Bring bricks online
        - Monitor heal
        - Check for split-brain
        - Validate IO
        """
        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))
        if offline_brick_list is None:
            raise Exception("Failed to get brick list")

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name,
                                           offline_brick_list):

            raise Exception("Failed to bring bricks offline")

        if not redant.are_bricks_offline(self.vol_name,
                                         offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are "
                            "not offline")

        # Create 50k files
        command = (f"cd {self.mountpoint}; "
                   "for i in `seq 1 50000` ; "
                   "do dd if=/dev/urandom of=test_$i "
                   "bs=1k count=1;done;")
        proc = redant.execute_command_async(command, self.client_list[0])

        # Validate IO
        mount_dict = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = self.redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Bring brick online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick_list):
            raise Exception("Failed to bring bricks online")

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name,
                                              timeout_period=3000):
            raise Exception("Heal has not yet completed")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")
