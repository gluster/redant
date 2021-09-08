"""
 Copyright (C) 2019  Red Hat, Inc. <http://www.redhat.com>

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
    Tests bricks EC version on a EC vol
    Bring down a brick and wait then bring down
    another brick and bring the first brick up healing
    should complete and EC version should be updated
"""

# disruptive;disp,dist-disp
from copy import deepcopy
from random import choice
from tests.d_parent_test import DParentTest


class TestEcVersionBrickdown(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        Create a directory on the mountpoint
        Create files on the mountpoint
        Bring down a brick say b1
        Create more files on the mountpoint
        Bring down another brick b2
        Bring up brick b1
        Wait for healing to complete
        Check if EC version is updated
        Check is EC size is updated
        """
        # Creating dir1 on the mountpoint
        redant.create_dir(self.mountpoint, "dir1", self.client_list[0])

        # Creating files on client side for dir1
        command = (f"cd {self.mountpoint}/dir1; for i in {{1..10}};do "
                   "dd if=/dev/urandom of=file.$i bs=1024 count=1000; done")
        proc = redant.execute_command_async(command, self.client_list[0])

        # Validating IO's and waiting to complete
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = redant.validate_io_procs(proc, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Bringing brick b1 offline
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols")

        bricks_list1 = choice(subvols)
        brick_b1_down = choice(bricks_list1)
        ret = redant.bring_bricks_offline(self.vol_name, brick_b1_down)
        if not ret:
            raise Exception(f"Brick {brick_b1_down} is not offline")

        # Creating files on client side for dir1
        command = (f"cd {self.mountpoint}/dir1; for i in {{11..20}};do "
                   "dd if=/dev/urandom of=file.$i bs=1024 count=1000; done")
        proc = redant.execute_command_async(command, self.client_list[0])

        # Validating IO's and waiting to complete
        ret = redant.validate_io_procs(proc, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Changing mode owner and group of files
        dir_file_range = '2..5'
        cmd = f"chmod 777 {self.mountpoint}/dir1/file.{dir_file_range}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f"chown root {self.mountpoint}/dir1/file.{dir_file_range}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f"chgrp root {self.mountpoint}/dir1/file.{dir_file_range}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create softlink and hardlink of files in mountpoint.
        cmd = (f"cd {self.mountpoint}/dir1/; for FILENAME in *; "
               "do ln -s $FILENAME softlink_$FILENAME; done;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = (f"cd {self.mountpoint}/dir1/; for FILENAME in *; "
               "do ln $FILENAME hardlink_$FILENAME; done;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bringing brick b2 offline
        bricks_list2 = deepcopy(bricks_list1)
        bricks_list2.remove(brick_b1_down)
        brick_b2_down = choice(bricks_list2)
        ret = redant.bring_bricks_offline(self.vol_name, brick_b2_down)
        if not ret:
            raise Exception(f"Brick {brick_b2_down} is not offline")

        # Bring brick b1 online
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         brick_b1_down)
        if not ret:
            raise Exception(f"Unable to bring brick {brick_b1_down} online")

        # Delete brick2 from brick list as we are not checking for heal
        # completion in brick 2 as it is offline

        bricks_list1.remove(brick_b2_down)

        # Check if EC version is same on all bricks which are up
        ret = redant.validate_xattr_on_all_bricks(bricks_list1, "dir1",
                                                  'trusted.ec.version')
        if not ret:
            raise Exception("EC version is not same on all bricks")

        # Check if EC size is same on all bricks which are up
        ret = redant.validate_xattr_on_all_bricks(bricks_list1, "dir1",
                                                  'trusted.ec.size')
        if not ret:
            raise Exception("EC size is not same on all bricks")
