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

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
   TC to check replace-brick functionality
"""

import random
from tests.d_parent_test import DParentTest

# disruptive;rep,dist-rep,disp,dist-disp


class TestCase(DParentTest):

    def test_glusterd_replace_brick(self, redant):
        """
        Create a volume and start it.
        - Get list of all the bricks which are online
        - Select a brick randomly from the bricks which are online
        - Form a non-existing brick path on node where the brick has to replace
        - Perform replace brick and it should fail
        - Form a new brick which valid brick path replace brick should succeed
        """
        # Getting all the bricks which are online
        bricks_online = redant.get_online_bricks_list(self.vol_name,
                                                      self.server_list[0])
        if bricks_online is None:
            raise Exception("Unable to get online brick list")

        # Getting one random brick from the online bricks to be replaced
        brick_to_replace = random.choice(bricks_online)
        node_of_brick_replace = brick_to_replace.split(':')[0]
        _, new_brick_to_replace = redant.form_brick_cmd(node_of_brick_replace,
                                                        self.brick_roots,
                                                        self.vol_name, 1)

        # performing replace brick with non-existing brick path
        path = ":/brick/non_existing_path"
        non_existing_path = node_of_brick_replace + path

        # Replace brick for non-existing path
        ret = redant.replace_brick(self.vol_name, brick_to_replace,
                                   non_existing_path, False)
        if ret['error_code'] == 0:
            raise Exception("Replace brick with commit force"
                            " on a non-existing brick passed")

        # calling replace brick by passing brick_to_replace and
        # new_brick_to_replace with valid brick path
        ret = redant.replace_brick_from_volume(self.vol_name,
                                               self.server_list[0],
                                               self.server_list,
                                               brick_to_replace,
                                               new_brick_to_replace)
        if not ret:
            raise Exception(f"Failed to replace brick: {brick_to_replace}")

        # Validating whether the brick replaced is online
        if not redant.wait_for_bricks_to_come_online(self.vol_name,
                                                     self.server_list,
                                                     new_brick_to_replace,
                                                     20):
            raise Exception("Replaced bricks is not yet online.")
