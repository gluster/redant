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
    TC to verify self-heal Triggers with self heal with heal command
"""

# disruptive;rep
# TODO: NFS, CIFS
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestVerifySelfHealTriggersHealCommand(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf['rep'])
        conf_hash['replica_count'] = 2
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

    def run_test(self, redant):
        """
        - set options:
          "metadata-self-heal": "off",
          "entry-self-heal": "off",
          "data-self-heal": "off",
          "self-heal-daemon": "off"
        - Bring brick 0 offline
        - Creating files on client side
        - Bring brick 0 online
        - Bring brick 1 offline
        - Creating files on client side
        - Bring brick 1 online
        - Get arequal on bricks
        - Setting option
          "self-heal-daemon": "on"
        - Start healing
        - Get arequal on bricks and compare with arequals before healing
          and mountpoint
        """
        # set options
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off",
                   "self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Bring brick 0 offline
        if not redant.bring_bricks_offline(self.vol_name, bricks_list[0]):
            raise Exception(f"Failed to bring brick {bricks_list[0]} offline")

        if not redant.are_bricks_offline(self.vol_name, bricks_list[0],
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_list[0]} is not offline")

        # Creating files on client side
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for mount_obj in self.mounts:
            # Create files
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      1, 0, 5, 1, 10,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Bring brick 0 online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          bricks_list[0]):
            raise Exception(f"Failed to bring bricks {bricks_list[0]} online")

        # Bring brick 1 offline
        if not redant.bring_bricks_offline(self.vol_name, bricks_list[1]):
            raise Exception(f"Failed to bring brick {bricks_list[1]} offline")

        if not redant.are_bricks_offline(self.vol_name, bricks_list[1],
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_list[1]} is not offline")

        # Creating files on client side
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for mount_obj in self.mounts:
            # Create files
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      6, 0, 5, 1, 10,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Bring brick 1 online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          bricks_list[1]):
            raise Exception(f"Failed to bring bricks {bricks_list[1]} online")

        # Get arequal on bricks
        arequals_before_heal = {}
        for brick in bricks_list:
            arequal = redant.collect_bricks_arequal(brick)
            brick_total = arequal[0][-1].split(':')[-1]
            arequals_before_heal[brick] = brick_total

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
            raise Exception("All process of volume are not online")

        # Wait for self-heal-daemons to be online
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Either No self heal daemon process found, "
                            "or more than one process found")

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception("Heal is not started")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Heal is not yet complete")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequals for mount
        arequals = redant.collect_mounts_arequal(self.mounts)
        mount_point_total = arequals[0][-1].split(':')[-1]

        # Get arequal on bricks and compare with mount_point_total
        # It should be the same
        arequals_after_heal = {}
        for brick in bricks_list:
            arequal = redant.collect_bricks_arequal(brick)
            brick_total = arequal[0][-1].split(':')[-1]
            arequals_after_heal[brick] = brick_total
            if brick_total != mount_point_total:
                raise Exception(f"Arequals for mountpoint and {brick} are not"
                                " equal")

        if arequals_before_heal == arequals_after_heal:
            raise Exception("Arequals are equal for bricks before "
                            f"({arequals_before_heal}) and after "
                            f"({arequals_after_heal}) healing")
