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
    Test cases in this module tests the authentication allow feature
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
from tests.d_parent_test import DParentTest


class TestFuseAuthAllow(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Create and start the volume
        """
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
        Verify auth.allow feature using client ip and hostname.
        Steps:
        1. Setup and start volume
        2. Set auth.allow on volume for client1 using ip of client1
        3. Mount volume on client1.
        4. Try to mount volume on client2. This should fail.
        5. Check the client2 logs for AUTH_FAILED event.
        6. Unmount the volume from client1.
        7. Set auth.allow on volume for client1 using hostname of client1.
        8. Repeat steps 3 to 5.
        9. Unmount the volume from client1.
        """
        # Check for 2 clients
        if len(self.client_list) < 2:
            self.TEST_RES = None
            raise Exception("The test case require 2 clients to run the test")

        # Setting authentication on volume for client1 using ip
        auth_dict = {'all': [self.client_list[0]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mounting volume on client1
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Trying to mount volume on client2
        redant.unauthenticated_mount(self.vol_name, self.server_list[0],
                                     self.mountpoint, self.client_list[1])

        # Verify whether mount failure on client2 is due to auth error
        prev_log_statement = redant.is_auth_failure(self.client_list[1])

        # Unmount volume from client1
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])

        # Obtain hostname of client1
        ret = redant.execute_abstract_op_node("hostname", self.client_list[0])
        hostname_client1 = ret['msg'][0].rstrip('\n')

        # Setting authentication on volume for client1 using hostname
        auth_dict = {'all': [hostname_client1]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mounting volume on client1
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Trying to mount volume on client2
        redant.unauthenticated_mount(self.vol_name, self.server_list[0],
                                     self.mountpoint, self.client_list[1])

        # Verify whether mount failure on client2 is due to auth error
        redant.is_auth_failure(self.client_list[1], prev_log_statement)

        # Unmount volume from client1
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])
