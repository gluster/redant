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
    TC to check data-self-heal-algorithm diff option when all other
    data-self-heal options are turned off
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
            "data-self-heal-algorithm": "diff"
            "self-heal-daemon": "off"
        - create IO
        - calculate arequal
        - bring down all bricks processes from selected set
        - modify the data
        - get arequal before getting bricks online
        - bring bricks online
        - expand volume by adding bricks to the volume
        - do rebalance
        - set the volume option "self-heal-daemon": "on" and check for daemons
        - start healing
        - check if heal is completed
        - check for split-brain
        - calculate arequal and compare with arequal before bringing bricks
          offline and after bringing bricks online
        """
        script_file_path = "/usr/share/redant/script/file_dir_ops.py"
        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off",
                   "data-self-heal-algorithm": "diff"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Creating files on client side
        mount_dict = []
        cmd = (f"python3 {script_file_path} create_files -f 100 "
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

        # Modify the data
        cmd = (f"python3 {script_file_path} create_files -f 100 "
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

        # Expand volume by adding bricks to the volume
        if not redant.expand_volume(self.server_list[0], self.vol_name,
                                    self.server_list, self.brick_roots):
            raise Exception("Failed to expand the volume when files present"
                            " on mountpoint")

        # Do rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        if not redant.wait_for_rebalance_to_complete(self.vol_name,
                                                     self.server_list[0]):
            raise Exception("Rebalance is not completed")

        # Setting options
        options = {"self-heal-daemon": "on"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

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
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Heal is not yet complete")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequal after getting bricks online
        result_after_online = redant.collect_mounts_arequal(mount_dict)

        # Checking arequals before bringing bricks offline
        # and after bringing bricks online
        if result_before_online != result_after_online:
            raise Exception("Checksums are not equal")
