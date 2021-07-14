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

# disruptive;dist-rep
# TODO: nfs, cifs

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
        - Create IO
        - While IO is creating - bring down a couple of bricks
        - Wait for IO to complete
        - Bring up the down bricks
        - Wait for heal to complete
        - Check for fields 'Brick', 'Status', 'Number of entries' in heal info
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Creating files on client side
        for mount_obj in self.mounts:
            # Create files
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      1, 2, 2, 2, 50,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Select bricks to bring offline
        bricks_to_bring_offline = (redant.
                                   select_volume_bricks_to_bring_offline(
                                       self.vol_name, self.server_list[0]))
        # Bring brick offline
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)
        if not (redant.
                are_bricks_offline(self.vol_name,
                                   bricks_to_bring_offline,
                                   self.server_list[0])):
            raise Exception(f"Bricks {bricks_to_bring_offline} are"
                            " still online")

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("Failed to validate IO")

        # Bring brick online
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_to_bring_offline)
        if not redant.are_bricks_online(self.vol_name, bricks_to_bring_offline,
                                        self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} not online.")

        # monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # is heal complete testing
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume in split-brain")

        # Get heal info
        heal_summ = redant.get_heal_info_summary(self.server_list[0],
                                                 self.vol_name)
        if heal_summ is None:
            raise Exception("Unable to get the heal info summary")

        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception('Failed to get the bricks list.')

        # Check all fields in heal info dict
        for brick in bricks_list:

            if heal_summ[brick]['status'] != 'Connected':
                raise Exception(f"Status is not connected for {brick}")

            if heal_summ[brick]['numberOfEntries'] != '0':
                raise Exception(f"numberOfEntries not 0 for {brick}")
