"""
Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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
    This test case deals with Arbiter self-heal tests.
"""

# disruptive;arb
# TODO: add nfs and cifs

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

    def _brick_operations(self, bricks_to_bring_offline: list):
        """
        brings the list of bricks offline and
        back online
        """
        self.redant.bring_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline)

        if not self.redant.are_bricks_offline(self.vol_name,
                                              bricks_to_bring_offline,
                                              self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} "
                            f"are not offline")

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
        - Create a 1x(2+1) arbiter replicate volume
        - Create IO
        - Bring down the 1-st data brick while creating IO
        - Bring up the 1-st data brick after creating and checking IO
        - Bring down the 3-d arbiter brick
        - Bring up the 3-d arbiter brick
        - Check there no any oom by listing the files from mountpoint
        """

        # Creating IO on client side
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.list_of_procs = []
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_files(num_files=1000,
                                       fix_fil_size="10k",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'])
            self.list_of_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # get the bricks for the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        # Bring brick 1 offline and then online
        bricks_to_bring_offline = [bricks_list[0]]
        self._brick_operations(bricks_to_bring_offline)

        # Bring brick 3 offline and then online
        bricks_to_bring_offline = [bricks_list[-1]]
        self._brick_operations(bricks_to_bring_offline)

        # Buffer to allow volume to be mounted
        sleep(4)

        # Get file list from mountpoint
        for mount_obj in self.mnt_list:
            file_list = redant.get_dir_contents(mount_obj['mountpath'],
                                                mount_obj['client'])
            if file_list is None:
                raise Exception("Empty directory")
