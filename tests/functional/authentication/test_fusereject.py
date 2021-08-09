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
    TC to validate the auth.reject volume option with "*" as value.
    FUSE Mount not allowed to the rejected client
"""

# disruptive;rep
from tests.d_parent_test import DParentTest


class TestAuthRejectVol(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        # Check server requirements
        self.redant.check_hardware_requirements(self.client_list, 2)

        # Create and start the volume
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node("mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)

    def run_test(self, redant):
        """
        -Set Authentication Reject for client1
        -Check if bricks are online
        -Mounting the vol on client1
        -Check if bricks are online
        -Mounting the vol on client2
        -Reset the Volume
        -Check if bricks are online
        -Mounting the vol on client1
        """
        # Obtain hostname of clients
        ret = redant.execute_abstract_op_node("hostname", self.client_list[0])
        hostname_client1 = ret['msg'][0].rstrip('\n')

        # Set Authentication
        auth_dict = {'all': [hostname_client1]}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Fetching all the bricks
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to get brick list")

        # Check are bricks online
        if not redant.are_bricks_online(self.vol_name, bricks_list,
                                        self.server_list[0]):
            raise Exception("All bricks are not online")

        # Using this way to check because of bug 1586036
        # Mounting volume
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0], excep=False)

        # Checking if volume is mounted
        if redant.is_mounted(self.vol_name, self.mountpoint,
                             self.client_list[0], self.server_list[0]):
            raise Exception("Unexpected: Mount executed successfully")

        # Checking client logs for authentication error
        cmd = (f"grep AUTH_FAILED /var/log/glusterfs/mnt-{self.vol_name}.log"
               " | wc -l")
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        if ret['msg'][0].rstrip('\n') == '0':
            raise Exception("Mounting has not failed due to"
                            "authentication error")

        # Mounting the vol on client2
        # Check bricks are online
        if not redant.are_bricks_online(self.vol_name, bricks_list,
                                        self.server_list[0]):
            raise Exception("All bricks are not online")

        # Mounting volume
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[1])

        # Checking if volume is mounted
        if not redant.is_mounted(self.vol_name, self.mountpoint,
                                 self.client_list[1], self.server_list[0]):
            raise Exception("Unexpected: Volume is not mounted")

        # Reset Volume
        redant.volume_reset(self.vol_name, self.server_list[0])

        # Checking if bricks are online
        if not redant.are_bricks_online(self.vol_name, bricks_list,
                                        self.server_list[0]):
            raise Exception("All bricks are not online")

        # Mounting Volume
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        # Checking if volume is mounted
        if not redant.is_mounted(self.vol_name, self.mountpoint,
                                 self.client_list[0], self.server_list[0]):
            raise Exception("Unexpected: Volume is not mounted")
