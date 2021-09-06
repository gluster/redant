"""
  Copyright (C) 2018  Red Hat, Inc. <http://www.redhat.com>

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

Test Description:
    Tests basic volume operations like ec volume create, start, stop, delete
    as part of setUp() and tearDown(). The function test_disperse_vol()
    verifies brick down, brick up scenarios and logs volume info and status.
"""

# disruptive;disp,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    # Tests: Kill 2 bricks and start it again
    def run_test(self, redant):
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        redant.bring_bricks_offline(self.vol_name, bricks_list[0:2])
        if not redant.are_bricks_offline(self.vol_name, bricks_list[0:2],
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_list[0:2]} is not offline")

        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_list[0:2])
        if not redant.are_bricks_online(self.vol_name, bricks_list[0:2],
                                        self.server_list[0]):
            raise Exception(f"Brick {bricks_list[0:2]} is not online")

        if not (redant.log_volume_info_and_status(self.server_list[0],
                                                  self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")
