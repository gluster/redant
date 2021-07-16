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
    TC to validate the auth.reject volume option with "*" as value. All
    clients will be rejected with this as value for auth.reject,then
    will reset the volume mount again.
"""

# disruptive;rep
from tests.d_parent_test import DParentTest


class TestAuthRejectVol(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        # Create and start the volume
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)

    def run_test(self, redant):
        """
        -Set Authentication
        -For all the clients
        -Fetch the bricks
        -Check if bricks are online
        -Create directory
        -Mount the volume
        -Check if it is mounted
        -Check authentication logs
        -Reset the Volume
        -Check if bricks are online
        -Mounting the vol on client1
        """
        # Set Authentication
        auth_dict = {'all': ['*']}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        for client in self.client_list:
            # Fetching all the bricks
            bricks_list = redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
            if bricks_list is None:
                raise Exception("Brick list is empty")

            # Check are bricks online
            if not redant.are_bricks_online(self.vol_name, bricks_list,
                                            self.server_list[0]):
                raise Exception("All bricks are not online")

            # Creating directory to mount
            self.mountpoint = "/mnt/testvol"
            redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                            client)

            # Using this way to check because of bug 1586036
            # Mounting volume
            redant.volume_mount(self.server_list[0], self.vol_name,
                                self.mountpoint, client, False)

            # Checking if volume is mounted
            if redant.is_mounted(self.vol_name, self.mountpoint,
                                 client, self.server_list[0]):
                raise Exception("Unexpected Mounting of Volume "
                                f" {self.vol_name} successful")

            # Checking client logs for authentication error
            cmd = "grep 'AUTH_FAILED' /var/log/glusterfs/mnt-testvol.log"
            redant.execute_abstract_op_node(cmd, client)

        # Reset Volume
        redant.volume_reset(self.vol_name, self.server_list[0])

        # Check if bricks are online and Mounting the vol on client1
        # Fetching bricks
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Brick list is empty")

        # Checking if bricks are online
        if not redant.are_bricks_online(self.vol_name, bricks_list,
                                        self.server_list[0]):
            raise Exception("All bricks are not online")

        # Mounting Volume
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        # Checking if Volume is mounted
        if not redant.is_mounted(self.vol_name, self.mountpoint,
                                 self.client_list[0], self.server_list[0]):
            raise Exception("Unexpected Mounting of Volume "
                            f" {self.vol_name} successful")
