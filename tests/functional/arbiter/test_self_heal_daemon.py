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
    TC to check self-heal-daemon option
"""

# disruptive;arb,dist-arb
from tests.d_parent_test import DParentTest


class TestSelfHealDaemon(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - Create directory test_hardlink_self_heal
        - Create directory test_data_self_heal
        - Creating files for hardlinks and data files
        - Get arequal before getting bricks offline
        - Select bricks to bring offline
        - Bring brick offline
        - Create hardlinks and append data to data files
        - Bring brick online
        - Wait for volume processes to be online
        - Verify volume's all process are online
        - Monitor heal completion
        - Check for split-brain
        - Get arequal after getting bricks online
        - Select bricks to bring offline
        - Bring brick offline
        - Truncate data to data files and verify hardlinks
        - Bring brick online
        - Wait for volume processes to be online
        - Verify volume's all process are online
        - Monitor heal completion
        - Check for split-brain
        - Get arequal again

        """
        # Creating directory test_hardlink_self_heal
        redant.create_dir(self.mountpoint, "test_hardlink_self_heal",
                          self.client_list[0])

        # Creating directory test_data_self_heal
        redant.create_dir(self.mountpoint, "test_data_self_heal",
                          self.client_list[0])

        # Creating files for hardlinks and data files
        cmd = (f"cd {self.mountpoint}/test_hardlink_self_heal;"
               "for i in `seq 1 5`; do mkdir dir.$i ; for j in `seq 1 10` ; "
               "do dd if=/dev/urandom of=dir.$i/file.$j bs=1k count=$j;done;"
               " done; cd ..")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = (f"cd {self.mountpoint}/test_data_self_heal;"
               "for i in `seq 1 100`; do dd if=/dev/urandom of=file.$i "
               "bs=128K count=$i;done; cd ..")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Mount dict for arequal-checksum op
        mount_dict = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Get arequal before getting bricks offline
        result_before_online = redant.collect_mounts_arequal(mount_dict)

        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name,
                                           offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        # Validate if bricks are offline
        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Append data to data files and create hardlinks
        cmd = (f"cd {self.mountpoint}/test_data_self_heal;"
               "for i in `seq 1 100`; do dd if=/dev/urandom of=file.$i "
               "bs=512K count=$i ; done ; cd ..")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = (f"cd {self.mountpoint}/test_hardlink_self_heal;"
               "for i in `seq 1 5` ;do for j in `seq 1 10`;do ln "
               "dir.$i/file.$j dir.$i/link_file.$j;done ; done ; cd ..")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bring bricks online
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
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequal after getting bricks online
        result_after_online = redant.collect_mounts_arequal(mount_dict)

        # Compare checksum
        if result_after_online != result_before_online:
            raise Exception("Arequal-checksum is not equal")

        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name,
                                           offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        # Validate if bricks are offline
        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Truncate data to data files and verify hardlinks
        cmd = (f"cd {self.mountpoint}/test_data_self_heal; "
               "for i in `seq 1 100`;do truncate -s $(( $i * 128)) file.$i;"
               " done ; cd ..")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        file_path = (f"{self.mountpoint}/test_hardlink_self_heal/"
                     "dir{1..5}/file{1..10}")
        link_path = (f"{self.mountpoint}/test_hardlink_self_heal/"
                     "dir{1..5}/link_file{1..10}")
        file_stat = redant.get_file_stat(self.client_list[0], file_path)
        link_stat = redant.get_file_stat(self.client_list[0], link_path)
        if file_stat != link_stat:
            raise Exception("Verification of hardlinks failed")

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
                                              self.vol_name):
            raise Exception("Heal has not yet completed")
