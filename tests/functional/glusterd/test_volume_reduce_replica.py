"""
  Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along`
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

  Description: Converting a 2x3 volume to a 2x2 volume and subsequently
  into a pure distribute volume.

"""

# disruptive;dist-rep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test case:
        1) Create a 2x3 replica volume.
        2) Remove bricks in the volume to make it a 2x2 replica volume.
        3) Remove bricks in the volume to make it a distribute volume.
        """
        self.brick_list = redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])

        remove_brick_list = [self.brick_list[0], self.brick_list[3]]
        redant.remove_brick(self.server_list[0], self.vol_name,
                            remove_brick_list, 'force', 2)
        redant.es.set_vol_type_param(self.vol_name, 'replica_count', -1)

        self.brick_list = redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])

        remove_brick_list = [self.brick_list[0], self.brick_list[2]]
        redant.remove_brick(self.server_list[0], self.vol_name,
                            remove_brick_list, 'force', replica_count=1)
        redant.es.set_vol_type_param(self.vol_name, 'replica_count', -1)

        if not redant.is_distribute_volume(self.vol_name):
            raise Exception(f"Volume {self.vol_name} is not a pure distribute"
                            " volume")
