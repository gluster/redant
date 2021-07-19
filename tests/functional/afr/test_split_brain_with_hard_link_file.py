"""
Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
    Test deals with checking split brain condition with hard link
    file.
"""

# disruptive;dist-rep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def _test_brick_down_with_file_rename(self, pfile, rfile, brick):
        # Bring brick offline
        self.redant.bring_bricks_offline(self.vol_name, brick)

        if not self.redant.are_bricks_offline(self.vol_name,
                                              [brick],
                                              self.server_list[0]):
            raise Exception(f'Brick {brick} is not offline')

        # Rename file
        cmd = (f"mv {self.mounts[0]['mountpath']}/{pfile} "
               f"{self.mounts[0]['mountpath']}/{rfile}")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bring brick back online
        self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                        [brick])
        if not self.redant.are_bricks_online(self.vol_name, [brick],
                                             self.server_list[0]):
            raise Exception(f"Brick {brick} is not online.")

    def run_test(self, redant):
        """
        Steps:
        1. Create  2 * 3 distribute replicate volume and disable all heals
        2. Create a file and 3 hardlinks to it from fuse mount.
        3. Kill brick4, rename HLINK1 to an appropriate name so that
           it gets hashed to replicate-1
        4. Likewise rename HLINK3 and HLINK7 as well, killing brick5 and brick6
           respectively each time. i.e. a different brick of the 2nd
           replica is down each time.
        5. Now enable shd and let selfheals complete.
        6. Heal should complete without split-brains.
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        bricks_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off",
                   "self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        cmd = f"touch {self.mounts[0]['mountpath']}/FILE"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Creating a hardlink for the file created
        for i in range(1, 4):
            if not (redant.
                    create_link_file(
                        self.client_list[0],
                        f'{self.mounts[0]["mountpath"]}/FILE',
                        f'{self.mounts[0]["mountpath"]}/HLINK{i}')):
                raise Exception("Unable to create hard link file.")

        # Bring brick3 offline,Rename file HLINK1,and bring back brick3 online
        self._test_brick_down_with_file_rename("HLINK1", "NEW-HLINK1",
                                               bricks_list[3])

        # Bring brick4 offline,Rename file HLINK2,and bring back brick4 online
        self._test_brick_down_with_file_rename("HLINK2", "NEW-HLINK2",
                                               bricks_list[4])

        # Bring brick5 offline,Rename file HLINK3,and bring back brick5 online
        self._test_brick_down_with_file_rename("HLINK3", "NEW-HLINK3",
                                               bricks_list[5])

        # Setting options
        options = {"self-heal-daemon": "on"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception('Heal is not started')

        # monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # is heal complete testing
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume in split-brain")

        # Check data on mount point
        if not redant.list_all_files_and_dirs_mounts([self.mounts[0]]):
            raise Exception("Can't find data on mount point")
