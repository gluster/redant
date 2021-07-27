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
    Tc to check self heal of files with different file types
    with default configuration
"""

# disruptive;arb,dist-arb
# TODO: NFS, CIFS
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - create IO
        - calculate arequal
        - bring down all bricks processes from selected set
        - calculate arequal and compare with arequal before getting
          bricks offline
        - modify the data
        - arequal before getting bricks online
        - bring bricks online
        - check daemons and healing completion
        - start healing
        - calculate arequal and compare with arequal before bringing bricks
          online and after bringing bricks online
        """
        # Creating files on client side
        test_folder = "test_file_type_differs_self_heal"

        # Creating files
        cmd = (f"cd {self.mountpoint}/ ; mkdir {test_folder}; "
               f"cd {test_folder}/; for i in `seq 1 10`;do mkdir l1_dir.$i; "
               "for j in `seq 1 5` ;do mkdir l1_dir.$i/l2_dir.$j; "
               "for k in `seq 1 10`; do dd if=/dev/urandom of=l1_dir.$i/"
               "l2_dir.$j/test.$k bs=1k count=$k; done; done; done;")

        proc = redant.execute_command_async(cmd, self.client_list[0])
        mount_dict = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Validate IO
        ret = self.redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Get arequal before getting bricks offline
        result_before_offline = redant.collect_mounts_arequal(mount_dict)

        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name, offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Get arequal after getting bricks offline
        result_after_offline = redant.collect_mounts_arequal(mount_dict)

        # Checking arequals before bringing bricks offline
        # and after bringing bricks offline
        if result_after_offline != result_before_offline:
            raise Exception("Checksums before and after bringing bricks"
                            " offline are not equal")

        # Modify the data
        cmd = (f"cd {self.mountpoint}/{test_folder}/ ;for i in `seq 1 10`; "
               "do for j in `seq 1 5`; do for k in `seq 1 10`; "
               "do rm -f l1_dir.$i/l2_dir.$j/test.$k; mkdir l1_dir.$i/"
               "l2_dir.$j/test.$k; done; done; done;")

        proc = redant.execute_command_async(cmd, self.client_list[0])

        # Validate IO
        ret = self.redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Get arequal before getting bricks online
        result_before_online = redant.collect_mounts_arequal(mount_dict)

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

        # Wait for self-heal-daemons to be online
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Failed to wait for self-heal deamon to be "
                            "online")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
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
