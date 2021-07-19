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
    Test cases related to
    healing in default configuration of the volume
"""

# disruptive;dist-rep

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
        - bring brick 1 offline
        - create files and validate IO
        - get entries before accessing file
        - get first filename from active subvol without offline bricks
        - access and modify the file
        - while accessing - get entries
        - Compare entries before accessing and while accessing
        - validate IO
        """
        self.all_mounts_procs = []
        self.counter = 1
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.bricks_list = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])

        # Bring 1-st brick offline
        brick_to_bring_offline = [self.bricks_list[0]]
        redant.bring_bricks_offline(self.vol_name, brick_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         brick_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Brick {brick_to_bring_offline}"
                            " is not offline")
        # Creating files on client side
        for mount_obj in self.mounts:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_files(num_files=100,
                                       fix_fil_size="1k",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'])

            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Get entries before accessing file
        entries_before_accessing = redant.get_heal_info_summary(
            self.server_list[0],
            self.vol_name)
        if entries_before_accessing is None:
            raise Exception("Failed to get the heal info summary")

        # Get filename to access from active subvol without offline bricks
        # Get last subvol
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        subvol_without_offline_brick = subvols[-1]

        # Get first brick server and brick path
        # and get first file from filelist
        subvol_mnode, mnode_brick = subvol_without_offline_brick[0].split(':')
        ret = redant.execute_abstract_op_node(f'ls {mnode_brick}',
                                              subvol_mnode)
        file_to_edit = ret['msg'][0].rstrip("\n")

        # Access and modify the file
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            cmd = (f"cd {mount_obj['mountpath']}/ ; "
                   f"dd if=/dev/zero of={file_to_edit} bs=1G count=1")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Get entries while accessing file
        entries_while_accessing = redant.get_heal_info_summary(
            self.server_list[0],
            self.vol_name)
        if entries_while_accessing is None:
            raise Exception("Failed to get the heal info summary")

        # Compare dicts before accessing and while accessing
        if entries_before_accessing != entries_while_accessing:
            raise Exception(f"Dictionaries before {entries_before_accessing} "
                            f"and while accessing {entries_while_accessing} "
                            "are different.")

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")
