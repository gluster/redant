"""
 Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

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
    Volume status when one of the brickpath is not available.
"""

import traceback
import random
from tests.d_parent_test import DParentTest

# disruptive;dist,rep,arb,dist-rep,disp,dist-arb,dist-disp


class TestCase(DParentTest):

    def terminate(self):
        # Remount the brick in case things fail midway
        try:
            if self.check_for_remount:
                self.redant.execute_abstract_op_node(f"mount "
                                                     f"{self.brick_path}",
                                                     self.brick_node)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test Case:
        1) Create a volume and start it.
        2) Fetch the brick list
        3) Bring any one brick down umount the brick
        4) Force start the volume and check that all the bricks are not online
        5) Remount the removed brick and bring back the brick online
        6) Force start the volume and check if all the bricks are online
        """
        self.check_for_remount = False

        # Fetching the brick list
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get the bricks in"
                            " the volume")

        # Bringing one brick down
        random_brick = random.choice(brick_list)
        if not redant.bring_bricks_offline(self.vol_name, random_brick):
            raise Exception("Failed to bring brick offline")

        # Creating a list of bricks to be removed
        remove_bricks_list = []
        remove_bricks_list.append(random_brick)

        # Checking if the brick is offline or not
        if not redant.are_bricks_offline(self.vol_name, remove_bricks_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {remove_bricks_list} are not offline")

        # umounting the brick which was made offline
        self.brick_node, volume_brick = random_brick.split(':')
        redant.logger.info("Brick: %s", volume_brick)
        self.brick_path = '/'.join(volume_brick.split('/')[0:3])
        redant.execute_abstract_op_node(f"umount {self.brick_path}",
                                        self.brick_node)
        self.check_for_remount = True

        # Force starting the volume
        redant.volume_start(self.vol_name, self.server_list[0], True)

        # remounting the offline brick
        redant.execute_abstract_op_node(f"mount {self.brick_path}",
                                        self.brick_node)
        self.check_for_remount = False

        # Checking that all the bricks shouldn't be online
        if redant.are_bricks_online(self.vol_name, brick_list,
                                    self.server_list[0]):
            raise Exception("Unexpected: Bricks are online")

        # Bringing back the offline brick online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          remove_bricks_list):
            raise Exception("Failed to bring bricks online")

        # Force starting the volume
        redant.volume_start(self.vol_name, self.server_list[0], True)

        # Checking if all the bricks are online or not
        if not redant.are_bricks_online(self.vol_name, brick_list,
                                        self.server_list[0]):
            raise Exception("All the bricks are not online")
