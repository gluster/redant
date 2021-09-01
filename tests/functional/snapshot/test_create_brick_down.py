"""
 Copyright (C) 2016-2017  Red Hat, Inc. <http://www.redhat.com>

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
    TC in this module tests for creating snapshot when the bricks are down.
"""

# disruptive;rep,dist,dist-rep
# TODO: NFS,CIFS
import random
from tests.d_parent_test import DParentTest


class TestCreateSnapwhenBricksareDown(DParentTest):

    def run_test(self, redant):
        """
        1. get brick list
        2. check all bricks are online
        3. Selecting one brick randomly to bring it offline
        4. get brick list
        5. check all bricks are online
        6. Offline Bricks list
        7. Online Bricks list
        8. Create snapshot of volume
        9. snapshot create should fail
        """
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])

        # check all bricks are online
        if not redant.are_bricks_online(self.vol_name, brick_list,
                                        self.server_list[0]):
            raise Exception("Not all bricks are online")

        # Selecting one brick randomly to bring it offline
        brick_to_bring_offline = random.choice(brick_list)
        if not redant.bring_bricks_offline(self.vol_name,
                                           brick_to_bring_offline):
            raise Exception("Failed to get brick offline")

        # get brick list
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])

        # check all bricks are not online
        if redant.are_bricks_online(self.vol_name, brick_list,
                                    self.server_list[0]):
            raise Exception("Unexpected: All bricks are online")

        # Offline Bricks list
        offbricks = redant.get_offline_bricks_list(self.vol_name,
                                                   self.server_list[0])
        if not offbricks:
            raise Exception("Failed to get the offline brick list")

        # Online Bricks list
        onbricks = redant.get_online_bricks_list(self.vol_name,
                                                 self.server_list[0])
        if not onbricks:
            raise Exception("Failed to get the online brick list")

        # Create snapshot of volume
        ret = redant.snap_create(self.vol_name, "snap1", self.server_list[0],
                                 False, "Description with $p3c1al character!",
                                 excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Snapshot creation is successful")

        # Volume status
        redant.get_volume_status(self.vol_name, self.server_list[0])

        # snapshot list
        redant.snap_list(self.server_list[0])
