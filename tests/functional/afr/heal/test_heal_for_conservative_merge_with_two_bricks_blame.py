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
    Test for conservative merge between two bricks.
"""

# disruptive;rep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1) Create 1x3 volume and fuse mount the volume
        2) On mount created a dir dir1
        3) Pkill glusterfsd on node n1 (b2 on node2 and b3 and node3 up)
        4) touch f{1..10} on the mountpoint
        5) b2 and b3 xattrs would be blaming b1 as files are created while
           b1 is down
        6) Reset the b3 xattrs to NOT blame b1 by using setattr
        7) Now pkill glusterfsd of b2 on node2
        8) Restart glusterd on node1 to bring up b1
        9) Now bricks b1 online , b2 down, b3 online
        10) touch x{1..10} under dir1 itself
        11) Again reset xattr on node3 of b3 so that it doesn't blame b2,
        as done for b1 in step 6
        12) Do restart glusterd on node2 hosting b2 to bring all bricks online
        13) Check for heal info, split-brain and arequal for the bricks
        """

        # Create dir `dir1/` on mountpoiint
        cmd = f"mkdir {self.mountpoint}/dir1"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        all_bricks = redant.get_online_bricks_list(self.vol_name,
                                                   self.server_list[0])
        brick1, brick2, brick3 = all_bricks

        # Bring first brick offline
        redant.bring_bricks_offline(self.vol_name, [brick1])
        if not redant.are_bricks_offline(self.vol_name,
                                         [brick1],
                                         self.server_list[0]):
            raise Exception(f'Brick {brick1} is not offline')

        # Create f{1..10} files on the mountpoint
        cmd = (f"cd {self.mountpoint}/dir1; for i in `seq 1 10`;"
               "do touch f$i; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check b2 and b3 xattrs are blaming b1 and are same
        first_xattr_to_reset = f"trusted.afr.{self.vol_name}-client-0"

        host, brick_path = brick2.split(":")
        fattr_from_br2 = redant.get_fattr(f'{brick_path}/dir1',
                                          first_xattr_to_reset, host)

        host, brick_path = brick3.split(":")
        fattr_from_br3 = redant.get_fattr(f'{brick_path}/dir1',
                                          first_xattr_to_reset, host)

        if (fattr_from_br2[1] != fattr_from_br3[1]):
            raise Exception("Both the bricks xattrs are not blaming"
                            " brick {brick1}")

        # Reset the xattrs of dir1 on b3 for brick b1
        xattr_value = "0x000000000000000000000000"
        redant.set_fattr(f'{brick_path}/dir1', first_xattr_to_reset,
                         host, xattr_value)

        # Kill brick2 on the node2
        redant.bring_bricks_offline(self.vol_name, [brick2])
        if not redant.are_bricks_offline(self.vol_name,
                                         [brick2],
                                         self.server_list[1]):
            raise Exception(f'Brick {brick2} is not offline')

        # Bring the brick1 online
        redant.restart_glusterd(self.server_list[0])
        if not (self.redant.
                wait_for_glusterd_to_start(self.server_list[0])):
            raise Exception(f"Glusterd still running on {self.server_list[0]}")

        if not redant.wait_for_bricks_to_come_online(self.vol_name,
                                                     self.server_list,
                                                     brick1):
            raise Exception("Brick {brick1} is not online")

        # Create 10 files under dir1 naming x{1..10}
        cmd = (f"cd {self.mountpoint}/dir1; for i in `seq 1 10`;"
               "do touch x$i; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Reset the xattrs from brick3 on to brick2
        second_xattr_to_reset = f"trusted.afr.{self.vol_name}-client-1"
        redant.set_fattr(f'{brick_path}/dir1', second_xattr_to_reset,
                         host, xattr_value)

        # Bring brick2 online
        redant.restart_glusterd(self.server_list[1])

        if not (self.redant.
                wait_for_glusterd_to_start(self.server_list[1])):
            raise Exception(f"Glusterd still running on {self.server_list[1]}")

        if not redant.wait_for_bricks_to_come_online(self.vol_name,
                                                     self.server_list,
                                                     brick2):
            raise Exception("Brick {brick2} is not online")

        # Check are there any files in split-brain and heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Conservative merge of files failed")

        # Check are there any files in split-brain and heal completion
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Some files are in split brain")

        # Check arequal checksum of all the bricks is same
        arequal = redant.collect_bricks_arequal(all_bricks)
        if len(set(tuple(x) for x in arequal)) != 1:
            raise Exception("Arequal is not same on all the bricks "
                            "in the subvol")
