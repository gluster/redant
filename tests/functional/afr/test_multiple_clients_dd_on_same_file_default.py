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

# disruptive;rep,arb
# TODO: NFS, CIFS

import traceback
from tests.d_parent_test import DParentTest


class TestVerifySelfHealTriggersHealCommand(DParentTest):

    def terminate(self):
        try:
            if not self.io_validation_complete:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mounts)):
                    raise Exception("IO failed on some of the clients")
            if not self.read_complete:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs_read, self.mounts)):
                    raise Exception("Reading failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        - Create 2GB file
        - While creating file, start reading file
        - Bring down brick1
        - Bring back the brick brick1
        - Start healing
        - Bring down brick1
        - Wait for IO to complete
        - Wait for reading to complete
        - Bring back the brick brick1
        - Start healing
        - Wait for heal to complete
        - Check for split-brain
        - Calculate arequals on all the bricks and compare with mountpoint
        """
        self.all_mounts_procs = []
        self.io_validation_complete = True
        self.read_complete = True
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Get brick list
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Brick list is None")

        # Creating files on client side
        for mount_obj in self.mounts:
            redant.logger.info(f"Generating data for {mount_obj['client']}"
                               f":{mount_obj['mountpath']}")
            # Create files
            command = (f"cd {mount_obj['mountpath']}; dd if=/dev/urandom "
                       "of=test_file bs=1M count=2020")
            proc = redant.execute_command_async(command, mount_obj['client'])
            self.all_mounts_procs.append(proc)
            self.io_validation_complete = False

        # Reading files on client side
        self.all_mounts_procs_read = []
        for mount_obj in self.mounts:
            command = ("python3 /tmp/file_dir_ops.py read "
                       f"{mount_obj['mountpath']}")

            proc = redant.execute_command_async(command, mount_obj['client'])
            self.all_mounts_procs_read.append(proc)
            self.read_complete = False

        # Bring brick1 offline
        redant.bring_bricks_offline(self.vol_name, brick_list[1])

        if not redant.are_bricks_offline(self.vol_name, brick_list[1],
                                         self.server_list[0]):
            raise Exception(f"Bricks {brick_list[1]} is not offline")

        # Bring brick1 online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          brick_list[1]):
            raise Exception(f"Failed to bring bricks {brick_list[1]} online")

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception('Heal is not started')

        # Bring brick1 offline
        redant.bring_bricks_offline(self.vol_name, brick_list[1])

        if not redant.are_bricks_offline(self.vol_name, brick_list[1],
                                         self.server_list[0]):
            raise Exception(f"Bricks {brick_list[1]} is not offline")

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")
        self.io_validation_complete = True

        # Validate reading
        if not redant.validate_io_procs(self.all_mounts_procs_read,
                                        self.mounts):
            raise Exception("Reading failed on some of the clients")
        self.read_complete = True

        # Bring brick1 online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          brick_list[1]):
            raise Exception(f"Failed to bring bricks {brick_list[1]} online")

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception('Heal is not started')

        # Monitor heal completion
        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name):
            raise Exception("Heal is not yet completed")

        # Check if heal is completed
        if not self.redant.is_heal_complete(self.server_list[0],
                                            self.vol_name):
            raise Exception("Heal is not completed")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequal for mount
        arequals = redant.collect_mounts_arequal(self.mounts)
        mount_point_total = arequals[0][-1].split(':')[-1]

        # Get arequal on bricks and compare with mount_point_total
        # It should be the same
        vol_info = redant.get_volume_info(self.server_list[0],
                                          self.vol_name)
        if vol_info is None:
            raise Exception("Unable to get volume info")

        if self.volume_type == "arb":
            data_brick_list = []
            for brick in brick_list:
                for brick_info in vol_info[self.vol_name]["bricks"]:
                    if brick_info["name"] == brick:
                        if brick_info["isArbiter"] == "0":
                            data_brick_list.append(brick)
            brick_list = data_brick_list

        for brick in brick_list:
            arequal = redant.collect_bricks_arequal(brick)
            brick_total = arequal[0][-1].split(':')[-1]
            if brick_total != mount_point_total:
                raise Exception(f"Arequals for mountpoint and {brick}"
                                " is not equal")
