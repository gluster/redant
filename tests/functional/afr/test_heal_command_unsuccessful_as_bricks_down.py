"""
Copyright (C) 2015-2018  Red Hat, Inc. <http://www.redhat.com>

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
"""

# disruptive;rep
# TODO: nfs, cifs addition

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _check_heal_error_message(self):
        cmd = f"gluster volume heal {self.vol_name}"
        ret = self.redant.execute_abstract_op_node(cmd,
                                                   self.server_list[0],
                                                   False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: heal started.")
        error_msg = ("Launching heal operation to perform index "
                     f"self heal on volume {self.vol_name} has been "
                     "unsuccessful")
        if error_msg not in ret['error_msg']:
            raise Exception("Error message is not present or is not valid")

    def run_test(self, redant):
        """
        - write 2 Gb file on mount
        - while write is in progress, kill brick b0
        - start heal on the volume (should fail and have error message)
        - bring up the brick which was down (b0)
        - bring down another brick (b1)
        - start heal on the volume (should fail and have error message)
        - bring bricks up
        - wait for heal to complete
        """
        self.all_mounts_procs = []
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to get the bricks list")

        # Creating files on client side
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Generating data for {mount_obj['client']}"
                               f":{mount_obj['mountpath']}")
            # Create 2 Gb file
            command = (f"cd {mount_obj['mountpath']} ; dd if=/dev/zero "
                       "of=file1  bs=10M  count=200")

            self.proc = redant.execute_command_async(command,
                                                     mount_obj['client'])
            self.all_mounts_procs.append(self.proc)

        # Bring brick0 offline
        redant.bring_bricks_offline(self.vol_name, [bricks_list[0]])

        if not (redant.
                are_bricks_offline(self.vol_name, [bricks_list[0]],
                                   self.server_list[0])):
            raise Exception(f"Bricks {bricks_list[0]} are not offline")

        # Start healing
        # Need to use 'gluster volume heal' command to check error message
        self._check_heal_error_message()

        # Bring brick0 online
        redant.bring_bricks_online(self.vol_name,
                                   self.server_list,
                                   [bricks_list[0]])
        if not redant.are_bricks_online(self.vol_name, [bricks_list[0]],
                                        self.server_list[0]):
            raise Exception(f"Failed to bring {bricks_list[0]} online")

        # Bring brick1 offline
        redant.bring_bricks_offline(self.vol_name, [bricks_list[1]])

        if not (redant.
                are_bricks_offline(self.vol_name, [bricks_list[1]],
                                   self.server_list[0])):
            raise Exception(f"Bricks {bricks_list[1]} are not offline")

        # Start healing
        # Need to use 'gluster volume heal' command to check error message
        self._check_heal_error_message()

        # Bring brick 1 online
        redant.bring_bricks_online(self.vol_name,
                                   self.server_list,
                                   [bricks_list[1]])
        if not redant.are_bricks_online(self.vol_name, [bricks_list[1]],
                                        self.server_list[0]):
            raise Exception(f"Failed to bring {bricks_list[1]} online")

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception("Heal is not started")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception('Heal is not complete')

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception('Volume is in split-brain state')

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs,
                                       self.mnt_list[0])
        if not ret:
            raise Exception("IO validation failed")
