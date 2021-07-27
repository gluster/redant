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
    TC to check Self-Heal of Symbolic Links (heal command)
"""

# disruptive;arb,dist-arb
# TODO: NFS
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - set the volume option
          "metadata-self-heal": "off"
          "entry-self-heal": "off"
          "data-self-heal": "off"
          "data-self-heal-algorithm": "diff"
          "self-heal-daemon": "off"
        - create IO
        - calculate arequal
        - bring down all bricks processes from selected set
        - calculate arequals and compare with arequal
          before bringing bricks offline
        - modify the data and verify whether the links are properly created
        - calculate arequal before getting bricks online
        - bring bricks online
        - set the volume option
          "self-heal-daemon": "on"
        - check daemons and start healing
        - check is heal is complited
        - check for split-brain
        - calculate arequal after getting bricks online and compare with
          arequal before getting bricks online
        """
        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off",
                   "self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Creating files on client side
        test_folder = "test_sym_link_self_heal"
        cmd = (f"cd {self.mountpoint}/ ; mkdir {test_folder}; "
               f"cd {test_folder}/ ;for i in `seq 1 5`; do mkdir dir.$i; "
               "for j in `seq 1 10`; do dd if=/dev/urandom of=dir.$i/file.$j"
               " bs=1k count=$j; done; done;")

        proc = redant.execute_command_async(cmd, self.client_list[0])

        # Validate IO
        mount_dict = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = self.redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Get arequal before getting bricks offline
        result_before_offline = redant.collect_mounts_arequal(mount_dict)

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

        # Get arequal after getting bricks offline
        result_after_offline = redant.collect_mounts_arequal(mount_dict)

        # Checking arequals before bringing bricks offline
        # and after bringing bricks offline
        if result_after_offline != result_before_offline:
            raise Exception("Checksums before and after bringing bricks "
                            "offline are not equal")

        # Modify the data
        # Create symlinks
        cmd = (f"cd {self.mountpoint}/{test_folder}/ ; "
               "for i in `seq 1 5`;do ln -s dir.$i sym_link_dir.$i ;done ;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Verify whether the links are properly created
        # Get symlink list
        cmd = f"cd {self.mountpoint}/{test_folder}/ ; ls |grep 'sym'"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        symlink_list = ret['msg']

        # Get folder list
        cmd = f"cd {self.mountpoint}/{test_folder}/ ; ls |grep -v 'sym'"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        folder_list = ret['msg']

        # Compare symlinks and folders
        for symlink in symlink_list:
            symlink_index = symlink_list.index(symlink)
            symlink = symlink.rstrip('\n')
            cmd = f"cd {self.mountpoint}/{test_folder}/ ; readlink {symlink}"
            ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
            symlink_to_folder = ret['msg'][0]
            if symlink_to_folder != folder_list[symlink_index]:
                raise Exception("Links are not properly created")

        # Get arequal before getting bricks online
        result_before_online = redant.collect_mounts_arequal(mount_dict)

        # Bring brick online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick_list):
            raise Exception("Failed to bring bricks online")

        # Setting options
        options = {"self-heal-daemon": "on"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Wait for volume processes to be online
        if not (redant.wait_for_self_heal_daemons_to_be_online(self.vol_name,
                self.server_list[0])):
            raise Exception("Self-heal process are not online")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Wait for self-heal-daemons to be online
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Either No self heal daemon process found")

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception("Heal is not started")

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
            raise Exception("Checksums before and after bringing bricks "
                            "online are not equal")
