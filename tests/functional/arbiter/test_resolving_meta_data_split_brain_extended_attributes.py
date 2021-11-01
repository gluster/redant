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
    Arbiter Test cases related to
    healing in default configuration of the volume
"""

# disruptive;dist-arb
# TODO: nfs, cifs

import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.list_of_procs,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _brick_and_io(self, bricks_to_bring_offline: list,
                      permission: str):
        """
        this functions brings brick offline
        performs permission change IO
        brings the brick back to online
        """
        # bring brick offline
        self.redant.bring_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline)

        if not self.redant.are_bricks_offline(self.vol_name,
                                              bricks_to_bring_offline,
                                              self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} "
                            f"are not offline")
        # Modify the data
        self.list_of_procs = []
        for mount_obj in self.mnt_list:
            # Modify the permissions
            cmd = (f"cd {mount_obj['mountpath']} ; "
                   f"chmod {permission}  test_file0.txt")

            proc = self.redant.execute_command_async(cmd,
                                                     mount_obj['client'])
            self.list_of_procs.append(proc)

        # Validate IO
        ret = self.redant.validate_io_procs(self.list_of_procs,
                                            self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # Bring the brick online
        self.redant.bring_bricks_online(self.vol_name,
                                        self.server_list,
                                        bricks_to_bring_offline)

        if not self.redant.are_bricks_online(self.vol_name,
                                             bricks_to_bring_offline,
                                             self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} "
                            f"are not online")

    def run_test(self, redant):
        """
        - Create a file test_file.txt
        - Find out which brick the file resides on and kill arbiter brick
        in the replica pair
        - Modify the permissions of the file
        - Bring back the killed brick
        - Kill the other brick in the replica pair
        - Modify the permissions of the file
        - Bring back the killed brick
        - Trigger heal
        - Check if heal is completed
        - Check for split-brain
        """
        # Creating files on client side
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        file_to_create = 'test_file'
        self.list_of_procs = []
        for mount_obj in self.mnt_list:
            proc = redant.create_files(num_files=1,
                                       fix_fil_size="1k",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'],
                                       base_file_name=file_to_create)
            self.list_of_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # get bricks with file
        subvols_dict = redant.get_subvols(self.vol_name, self.server_list[0])
        brick_list_with_file = []
        for subvol in subvols_dict:
            for brick in subvol:
                node, brick_path = brick.split(':')
                brick_file_list = redant.get_dir_contents(brick_path, node)
                if 'test_file0.txt' in brick_file_list:
                    brick_list_with_file.append(brick)

        # Bring arbiter brick offline
        bricks_to_bring_offline = [brick_list_with_file[-1]]
        self._brick_and_io(bricks_to_bring_offline, "600")

        # Buffer to allow volume to be mounted
        sleep(4)

        # Bring 1-st data brick offline
        bricks_to_bring_offline = [brick_list_with_file[0]]
        self._brick_and_io(bricks_to_bring_offline, "644")

        # Start healing
        if not redant.trigger_heal(self.vol_name,
                                   self.server_list[0]):
            raise Exception("Heal did not trigger")

        # monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # is heal complete testing
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet completed")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")
