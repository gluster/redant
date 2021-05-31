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

Desciption: To check fix-layout operation and the xattr on a dir in brick.
"""

import traceback
from tests.nd_parent_test import NdParentTest

# nonDisruptive;dist


class TestCase(NdParentTest):

    def terminate(self):
        """
        To check whether the brick remove was stopped or not
        """
        try:
            if not self.check_flag:
                self.redant.remove_brick(self.server_list[0], self.vol_name,
                                         self.brick_list[1:2], 'stop')
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        In this test case:
        1. Remove a brick from the volume
        2. Check remove-brick status
        3. Stop the remove brick process
        4. Perform fix-layoyt on the volume
        5. Get the rebalance fix-layout status
        6. Create a directory from mount point
        7. Check trusted.glusterfs.dht extended attribue for newly
           created directory on the remove brick
        """
        self.check_flag = False
        self.brick_list = redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])

        redant.remove_brick(self.server_list[0], self.vol_name,
                            self.brick_list[1:2], 'start')

        redant.remove_brick(self.server_list[0], self.vol_name,
                            self.brick_list[1:2], 'stop')
        self.check_flag = True
        redant.rebalance_start(self.vol_name, self.server_list[0], True)
        if not redant.wait_for_fix_layout_to_complete(self.server_list[0],
                                                      self.vol_name):
            raise Exception(f"Fix layout not completed for {self.vol_name}")

        redant.create_dir(self.mountpoint, "dir1", self.client_list[0])
        folder_name = (f"{self.brick_list[1].split(':')[1]}/dir1")
        redant.get_fattr(folder_name, 'trusted.glusterfs.dht',
                         self.brick_list[1].split(':')[0])
