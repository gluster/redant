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

Description:
    Verify that files created from the backend without gfid gets assigned one
    and are healed when accessed from the client.
"""
# disruptive;rep

import time
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def _verify_gfid_and_link_count(self, dirname, filename):
        """
        check that the dir and all files under it have the same gfid on all 3
        bricks and that they have the .glusterfs entry as well.
        """
        dir_gfids = dict()
        file_gfids = dict()
        for brick in self.bricks_list:
            brick_node, brick_path = brick.split(":")

            ret = self.redant.get_fattr(f'{brick_path}/{dirname}',
                                        'trusted.gfid', brick_node)

            dir_gfids.setdefault(dirname, []).append(ret[1])

            ret = self.redant.get_fattr(f'{brick_path}/{dirname}/{filename}',
                                        'trusted.gfid', brick_node)
            file_gfids.setdefault(filename, []).append(ret[1])

            stat_data = (self.redant.
                         get_file_stat(
                             brick_node,
                             f"{brick_path}/{dirname}/{filename}"))['msg']
            if stat_data['st_nlink'] != 2:
                raise Exception("Link count not 2")

        if len(set(dir_gfids[dirname])) != 1:
            raise Exception(f"GFID mismatched for dir {dirname}")

        if len(set(file_gfids[filename])) != 1:
            raise Exception(f"GFID mismatched for file {filename}")

    def run_test(self, redant):
        """
        - Create a 1x3 volume and fuse mount it.
        - Create 1 directory with 1 file inside it directly on each brick.
        - Access the directories from the mount.
        - Launch heals and verify that the heals are over.
        - Verify that the files and directories have gfid assigned.
        """
        # Create data on the bricks.
        self.bricks_list = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        i = 0
        for brick in self.bricks_list:
            i += 1
            brick_node, brick_path = brick.split(":")
            redant.create_dir(brick_path, f"dir{i}", brick_node)
            if not redant.create_file(f"{brick_path}/dir{i}/", f"file{i}",
                                      brick_node):
                raise Exception(f"File creation failed on {brick_node}")

        # To circumvent is_fresh_file() check in glusterfs code.
        time.sleep(2)

        # Access files from mount
        for i in range(1, 4):
            cmd = f"ls {self.mountpoint}/dir{i}/file{i}"
            redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Trigger heal
        if not (redant.
                trigger_heal(self.vol_name, self.server_list[0])):
            raise Exception("Failed to trigger heal")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        # Verify gfid and links at the backend.
        self._verify_gfid_and_link_count("dir1", "file1")
        self._verify_gfid_and_link_count("dir2", "file2")
        self._verify_gfid_and_link_count("dir3", "file3")
