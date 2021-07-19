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
    Verify self-heal Triggers with self heal with heal command
"""

# disruptive;rep

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        - set "entry-self-heal", "metadata-self-heal", "data-self-heal" to off
        - write a few files
        - bring down brick0
        - add IO
        - do a heal info and check for files pending heal on last 2 bricks
        - set "performance.enable-least-priority" to "enable"
        - bring down brick1
        - set the "quorum-type" to "fixed"
        - add IO
        - do a heal info and check for files pending heal on the last brick
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Creating files on client side
        for mount_obj in self.mounts:
            # Create files
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_files(num_files=10,
                                       fix_fil_size="1M",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'])

            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Bring brick0 offline
        redant.bring_bricks_offline(self.vol_name, bricks_list[0])

        if not redant.are_bricks_offline(self.vol_name,
                                         [bricks_list[0]],
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_list[0]} are not offline")

        # Creating files on client side
        number_of_files_one_brick_off = 1000
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # Create files
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_files(num_files=number_of_files_one_brick_off,
                                       fix_fil_size="1k",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'],
                                       base_file_name="new_file")

            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Get heal info
        heal_info_data = redant.get_heal_info_summary(self.server_list[0],
                                                      self.vol_name)
        if heal_info_data is None:
            raise Exception("Failed to get heal info summary")

        # Check quantity of file pending heal
        for brick in bricks_list[1:]:
            if heal_info_data[brick]['numberOfEntries'] != '1001':
                raise Exception("Number of files pending heal is incorrect")

        # Setting options
        options = {"performance.enable-least-priority": "enable"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Bring brick1 offline
        redant.bring_bricks_offline(self.vol_name, bricks_list[1])

        if not redant.are_bricks_offline(self.vol_name,
                                         [bricks_list[1]],
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_list[1]} is not offline")

        # Setting options
        options = {"quorum-type": "fixed"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Creating files on client side
        number_of_files_two_brick_off = 100
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_files(num_files=number_of_files_two_brick_off,
                                       fix_fil_size="1k",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'],
                                       base_file_name="new_new_file")

            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Get heal info
        heal_info_data = redant.get_heal_info_summary(self.server_list[0],
                                                      self.vol_name)
        if heal_info_data is None:
            raise Exception("Failed to get heal info summary")

        # Check quantity of file pending heal
        number_of_files_to_check = (number_of_files_one_brick_off
                                    + number_of_files_two_brick_off + 1)
        if (heal_info_data[bricks_list[-1]]['numberOfEntries']
           != str(number_of_files_to_check)):
            raise Exception('Number of files pending heal is not correct')
