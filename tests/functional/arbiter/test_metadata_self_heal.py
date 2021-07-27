"""
 Copyright (C) 2015-2021 Red Hat, Inc. <http://www.redhat.com>

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
    TC to test metadata self-heal
"""

# disruptive;arb,dist-arb
# TODO: NFS
from tests.d_parent_test import DParentTest


class TestMetadataSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - set the volume option
          "metadata-self-heal": "off"
          "entry-self-heal": "off"
          "data-self-heal": "off"
        - create IO
        - set the volume option - "self-heal-daemon": "off"
        - bring down all bricks processes from selected set
        - Change the permissions, ownership and the group
          of the files under "test_meta_data_self_heal" folder
        - get arequal before getting bricks online
        - bring bricks online
        - set the volume option - "self-heal-daemon": "on"
        - check daemons and start healing
        - check is heal is completed
        - check for split-brain
        - get arequal after getting bricks online and compare with
          arequal before getting bricks online
        - check group and user are 'qa'
        """
        # Create a new user
        all_nodes = self.server_list + self.client_list
        if not redant.add_user(all_nodes, "test"):
            raise Exception("Failed to add user 'test'")

        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Creating files on client side
        test_folder = 'test_meta_data_self_heal'

        # Create files
        cmd = (f"cd {self.mountpoint}/ ; mkdir {test_folder}; "
               f"cd {test_folder}/ ; for i in `seq 1 50` ; "
               "do dd if=/dev/urandom of=test.$i bs=10k count=1 ; done ;")

        proc = redant.execute_command_async(cmd, self.client_list[0])
        mount_dict = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Validate IO
        ret = self.redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Setting options
        options = {"self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name, offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Changing the permissions, ownership and the group
        # of the files under "test_meta_data_self_heal" folder
        # Change permissions to 444
        cmd = f"cd {self.mountpoint}/{test_folder}/ ; chmod -R 444 *"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Change the ownership to user 'test'
        cmd = f"cd {self.mountpoint}/{test_folder}/ ; chown -R test *"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Change the group to test
        cmd = f"cd {self.mountpoint}/{test_folder}/ ; chgrp -R test *"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

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

        # Adding servers and client in single dict to check permissions
        nodes_to_check = {}
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if all_bricks is None:
            raise Exception("Failed to get the brick list")

        for brick in all_bricks:
            node, brick_path = brick.split(':')
            nodes_to_check[node] = brick_path

        nodes_to_check[self.client_list[0]] = self.mountpoint

        # Checking for user and group
        for node in nodes_to_check:
            # Get file list
            cmd = f"cd {nodes_to_check[node]}/{test_folder}/ ; ls"
            ret = redant.execute_abstract_op_node(cmd, node)
            file_list = ret['msg']

            for file_name in file_list:
                file_name = file_name.strip()
                file_to_check = (f"{nodes_to_check[node]}/{test_folder}/"
                                 f"{file_name}")

                # Check for permissions
                cmd = (f"stat -c '%a %n' {file_to_check} "
                       "| awk '{{print $1}}'")
                ret = redant.execute_abstract_op_node(cmd, node)
                if ret['msg'][0].strip() != "444":
                    raise Exception("Permissions is not equal to 444")

                # Check for user
                cmd = (f"ls -ld {file_to_check} | "
                       "awk '{{print $3}}'")
                ret = redant.execute_abstract_op_node(cmd, node)
                if ret['msg'][0].strip() != "test":
                    raise Exception("User is not equal 'test'")

                # Check for group
                cmd = (f"ls -ld {file_to_check} | "
                       "awk '{{print $4}}'")
                ret = redant.execute_abstract_op_node(cmd, node)
                if ret['msg'][0].strip() != "test":
                    raise Exception("Group is not equal 'test'")
