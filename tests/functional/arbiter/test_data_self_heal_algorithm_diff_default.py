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
    TC to check data-self-heal-algorithm diff option
"""

# disruptive;rep,dist-rep,arb,dist-arb
# TODO: NFS,CIFS
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - set the volume option "data-self-heal-algorithm" to value "diff"
        - create IO
        - bring down all bricks processes from selected set
        - modify the data
        - calculate arequal
        - bring bricks online
        - start healing
        - calculate arequal and compare with arequal before bringing bricks
        offline and after bringing bricks online
        """
        # Setting options
        options = {"data-self-heal-algorithm": "diff"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Creating files on client side
        mount_dict = []
        cmd = ("python3 /tmp/file_dir_ops.py create_files -f 100 "
               f"{self.mountpoint}")

        proc = redant.execute_command_async(cmd, self.client_list[0])
        mount_dict.append({
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        })

        # Validate IO
        ret = self.redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name, offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Modify the data
        cmd = ("python3 /tmp/file_dir_ops.py create_files -f 100 "
               f" --fixed-file-size 1M {self.mountpoint}")

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
            raise Exception("All process are not online")

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
        if result_before_online != result_after_online:
            raise Exception("Checksums are not equal")
