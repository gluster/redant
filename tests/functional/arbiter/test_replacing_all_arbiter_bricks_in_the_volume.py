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

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        - Create an arbiter volume 4(2+1) distributed replicate
        - Start writing IO
        - While the I/O's are going on replace all the arbiter bricks
        - check for the new bricks attached successfully
        - Check for heals
        - Validate IO
        """
        # get the bricks for the volume
        self.all_mounts_procs = []
        self.bricks_to_clean = []
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Bricks list is none")

        # Clear all brick folders. Its need to prevent healing with old files
        for brick in bricks_list:
            redant.logger.info(f'Clearing brick {brick}')
            node, brick_path = brick.split(':')
            redant.execute_abstract_op_node(f'cd {brick_path}/ ; rm -rf *',
                                            node)

        # Creating files on client side
        self.mounts = (redant.es.
                       get_mnt_pts_dict_in_list(self.vol_name))
        counter = 1

        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 3, 3, 3, 20,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter = counter + 20

        # replace bricks
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        for subvol in subvols:
            redant.logger.info(f'Replacing arbiter brick for {subvol}')
            brick_to_replace = subvol[-1]
            new_brick = brick_to_replace + 'new'
            redant.logger.info(f"Replacing the brick {brick_to_replace} "
                               f"for the volume: {self.vol_name}")
            redant.replace_brick(self.server_list[0],
                                 self.vol_name,
                                 brick_to_replace, new_brick)
            self.bricks_to_clean.append(brick_to_replace)

        # check replaced bricks
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        index = 0
        for subvol in subvols:
            expected_brick_path = self.bricks_to_clean[index]+'new'
            brick_to_check = subvol[-1]
            if expected_brick_path != brick_to_check:
                raise Exception(f"Brick {brick_to_check} is not"
                                " replaced brick")
            index += 1

        # Wait for volume processes to be online
        if not (redant.
                wait_for_volume_process_to_be_online(self.vol_name,
                                                     self.server_list[0],
                                                     self.server_list)):
            raise Exception(f"Failed to wait for volume {self.vol_name} "
                            "processes to be online")

        # Verify volume's all process are online
        if not (redant.
                verify_all_process_of_volume_are_online(self.vol_name,
                                                        self.server_list[0])):
            raise Exception(f"Volume {self.vol_name}: All process"
                            " are not online")

        # Wait for self-heal-daemons to be online
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Either No self heal daemon process found")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception('Heal has not yet completed')

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal is not complete")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception('Volume is in split-brain state')

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs,
                                       self.mounts)
        if not ret:
            raise Exception("IO validation failed")
