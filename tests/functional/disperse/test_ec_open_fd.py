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
    Tests open FD heal for EC volume
"""

# disruptive;disp,dist-disp
from random import choice
from tests.d_parent_test import DParentTest


class TestEcOpenFd(DParentTest):

    def run_test(self, redant):
        """
        Test Steps:
        - disable server side heal
        - Create a file
        - Set volume option to implement open FD on file
        - Bring a brick down,say b1
        - Open FD on file
        - Bring brick b1 up
        - write to open FD file
        - Monitor heal
        - Check xattr , ec.version and ec.size of file
        - Check stat of file
        """
        # Disable server side heal
        ret = redant.disable_heal(self.server_list[0], self.vol_name)
        if not ret:
            raise Exception("Failed to disable server side heal")

        # Log Volume Info and Status after disabling server side heal
        if not (redant.log_volume_info_and_status(self.server_list[0],
                                                  self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Create a file
        cmd = f"cd {self.mountpoint}; touch 'file_openfd';"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Set volume options
        options = {"performance.read-after-open": "yes"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Bringing brick b1 offline
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed ot get the subvols list")

        bricks_list1 = subvols[0]
        brick_b1_down = choice(bricks_list1)
        ret = redant.bring_bricks_offline(self.vol_name, brick_b1_down)
        if not ret:
            raise Exception(f"Brick {brick_b1_down} is not offline")

        # Open FD
        proc = redant.open_file_fd(self.mountpoint, time=100,
                                   client=self.client_list[0])

        # Bring brick b1 online
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         brick_b1_down)
        if not ret:
            raise Exception(f"Brick {brick_b1_down} is not brought online")

        # Validate peers are connected
        ret = redant.validate_peers_are_connected(self.server_list)
        if not ret:
            raise Exception("Peers are not in connected state")

        # Check if write to FD is successful
        ret = redant.wait_till_async_command_ends(proc)
        if ret['error_code'] != 0:
            raise Exception("Write to FD is unsuccessful")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        file_openfd = f"{self.mountpoint}/file_openfd"

        # Check if data exists on file
        ret = redant.check_if_pattern_in_file(self.client_list[0], 'xyz',
                                              file_openfd)
        if ret != 0:
            raise Exception('xyz does not exists in file')

        file_fd = 'file_openfd'

        # Check if EC version is same on all bricks which are up
        ret = redant.validate_xattr_on_all_bricks(bricks_list1, file_fd,
                                                  'trusted.ec.version')
        if not ret:
            raise Exception("Healing not completed and EC version is "
                            "not updated")

        # Check if EC size is same on all bricks which are up
        ret = redant.validate_xattr_on_all_bricks(bricks_list1, file_fd,
                                                  'trusted.ec.size')
        if not ret:
            raise Exception("Healing not completed and EC size is "
                            "not updated")

        # Check stat of file
        cmd = f"cd {self.mountpoint}; du -kh file_openfd"
        redant.execute_abstract_op_node(cmd, self.client_list[0])
