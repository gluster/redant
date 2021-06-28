"""
Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>

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

Description: TC to check that remove brick commit fails during rebalance.
"""

from tests.d_parent_test import DParentTest

# disruptive;dist-rep


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        In this test case:
        1. Create some data file
        2. Start remove-brick operation for one replica pair
        3. Restart glusterd on all nodes
        4. Try to commit the remove-brick operation while rebalance
           is in progress, it should fail
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        counter = 1
        for mount in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 5, 5, 10,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter += 10

        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO operations failed on some or all of the"
                            " clients")

        self.bricks_list = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        if self.bricks_list is None:
            raise Exception(f"Brick list for {self.vol_name} is None")

        remove_brick_list = self.bricks_list[3:6]
        redant.remove_brick(self.server_list[0], self.vol_name,
                            remove_brick_list, 'start', 3)
        redant.restart_glusterd(self.server_list)
        if not redant.wait_for_glusterd_to_start(self.server_list):
            raise Exception(f"Failed to start glusterd on {self.server_list}")

        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  remove_brick_list, 'commit', 3, False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Brick commit should've failed!")
