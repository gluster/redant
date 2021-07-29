"""
 Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check self-heal of 50k files by add-brick
"""

# disruptive;arb,dist-arb
# TODO: NFS
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        Test self-heal of 50k files (heal command)
        Description:
        - Set the volume option
          "metadata-self-heal": "off"
          "entry-self-heal": "off"
          "data-self-heal": "off"
          "self-heal-daemon": "off"
        - Bring down all bricks processes from selected set
        - Create IO (50k files)
        - Get arequal before getting bricks online
        - Bring bricks online
        - Set the volume option
          "self-heal-daemon": "on"
        - Check for daemons
        - Start healing
        - Check if heal is completed
        - Check for split-brain
        - Get arequal after getting bricks online and compare with
          arequal before getting bricks online
        - Add bricks
        - Do rebalance
        - Get arequal after adding bricks and compare with
          arequal after getting bricks online
        """
        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off",
                   "self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name,
                                           offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Creating files on client side
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

        # Get arequal before getting bricks online
        result_before_online = redant.collect_mounts_arequal(mount_dict)

        # Bring brick online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick_list):
            raise Exception("Failed to bring bricks online")

        # Setting options
        redant.set_volume_options(self.vol_name, {"self-heal-daemon": "on"},
                                  self.server_list[0])

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Wait for self-heal-daemons to be online
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Failed to wait for self-heal deamon to be "
                            "online")

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception("Heal is not started")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal is not yet complete")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequal after getting bricks online
        result_after_online = redant.collect_mounts_arequal(mount_dict)

        # Checking arequals before bringing bricks online
        # and after bringing bricks online
        if result_after_online != result_before_online:
            raise Exception("Checksums before and after bringing bricks"
                            " online are not equal")

        # Add bricks
        if not redant.expand_volume(self.server_list[0], self.vol_name,
                                    self.server_list, self.brick_roots):
            raise Exception(f"Failed to expand the volume {self.vol_name}")

        # Do rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0])

        if not redant.wait_for_rebalance_to_complete(self.vol_name,
                                                     self.server_list[0],
                                                     timeout=3600):
            raise Exception("Rebalance is not completed")

        # Get arequal after adding bricks
        result_after_adding_bricks = redant.collect_mounts_arequal(mount_dict)

        # Checking arequals after bringing bricks online
        # and after adding bricks
        if result_after_adding_bricks != result_after_online:
            raise Exception("Checksums after bringing bricks online"
                            " and after adding bricks are not equal")
