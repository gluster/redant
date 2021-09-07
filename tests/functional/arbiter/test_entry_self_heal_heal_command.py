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
    TC to test the entry-self-heall command in gluster
"""

# disruptive;arb,dist-arb
# TODO: NFS,CIFS
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - set the volume option
          "metadata-self-heal": "off"
          "entry-self-heal": "off"
          "data-self-heal": "off"
        - create IO
        - get arequal before getting bricks offline
        - set the volume option - "self-heal-daemon": "off"
        - bring down all bricks processes from selected set
        - get arequal after getting bricks offline and compare with
          arequal after bringing bricks offline
        - modify the data
        - get arequal before getting bricks online
        - bring bricks online
        - set the volume option
          "self-heal-daemon": "on"
        - check daemons and start healing
        - check if heal is completed
        - check for split-brain
        - get arequal after getting bricks online and compare with
          arequal before bringing bricks online
        """
        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Start IO on mounts
        # Creating files on client side
        proc = redant.create_deep_dirs_with_files(self.mountpoint, 0, 2, 2,
                                                  2, 20, self.client_list[0])
        mount_dict = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        script_file_path = "/usr/share/redant/script/file_dir_ops.py"
        # Command list to do different operations with data -
        # create, rename, copy and delete
        cmds = (
            (f"python3 {script_file_path} create_files -f 20 "
             f"{self.mountpoint}/files"),
            f"python3 {script_file_path} mv {self.mountpoint}/files",
            (f"python3 {script_file_path} copy --dest-dir "
             f"{self.mountpoint}/new_dir {self.mountpoint}/files"),
            f"python3 {script_file_path} delete {self.mountpoint}",
        )
        for cmd in cmds:
            # Get arequal before getting bricks offline
            arequal = redant.collect_mounts_arequal(mount_dict)
            result_before_offline = arequal[0][-1].split(':')[-1]

            # Setting options
            options = {"self-heal-daemon": "off"}
            redant.set_volume_options(self.vol_name, options,
                                      self.server_list[0])

            # Select bricks to bring offline
            offln_brick_list = (redant.select_volume_bricks_to_bring_offline(
                                self.vol_name, self.server_list[0]))

            # Bring brick offline
            if not redant.bring_bricks_offline(self.vol_name,
                                               offln_brick_list):
                raise Exception("Failed to bring bricks offline")

            if not redant.are_bricks_offline(self.vol_name, offln_brick_list,
                                             self.server_list[0]):
                raise Exception(f"Bricks {offln_brick_list} are not offline")

            # Get arequal after getting bricks offline
            arequal = redant.collect_mounts_arequal(mount_dict)
            result_after_offline = arequal[0][-1].split(':')[-1]

            # Checking arequals before bringing bricks offline
            # and after bringing bricks offline
            if result_after_offline != result_before_offline:
                raise Exception('Checksums are not equal')

            # Modify the data
            redant.execute_abstract_op_node(cmd, self.client_list[0])

            # Get arequal before getting bricks online
            arequal = redant.collect_mounts_arequal(mount_dict)
            result_before_online = arequal[0][-1].split(':')[-1]

            # List all files and dirs created
            if not redant.list_all_files_and_dirs_mounts(mount_dict):
                raise Exception("Failed to list all files and dirs")

            # Bring brick online
            if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                              offln_brick_list):
                raise Exception("Failed to bring bricks online")

            # Setting options
            options = {"self-heal-daemon": "on"}
            redant.set_volume_options(self.vol_name, options,
                                      self.server_list[0])

            # Wait for volume processes to be online
            if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                    self.server_list[0], self.server_list)):
                raise Exception("Failed to wait for volume processes to "
                                "be online")

            # Verify volume's all process are online
            if not (redant.verify_all_process_of_volume_are_online(
                    self.vol_name, self.server_list[0])):
                raise Exception("All process are not online")

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
            arequal = redant.collect_mounts_arequal(mount_dict)
            result_after_online = arequal[0][-1].split(':')[-1]

            # List all files and dirs created
            if not redant.list_all_files_and_dirs_mounts(mount_dict):
                raise Exception("Failed to list all files and dirs")

            # Checking arequals before bringing bricks online
            # and after bringing bricks online
            if result_before_online != result_after_online:
                raise Exception('Checksums are not equal')
