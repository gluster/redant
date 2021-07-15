"""
 Copyright (C) 2021  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check the authentication allow feature
    using auth.allow and auth.reject volume option on same client
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
from tests.d_parent_test import DParentTest


class TestFuseAuthRejectAllow(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        # Check for 2 clients
        if len(self.client_list) < 2:
            self.TEST_RES = None
            raise Exception("The test case require 2 clients to run the test")

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
        Verify auth.reject and auth.allow volume options in volume level using
        both client ip and hostname.
        Steps:
        1. Create and start volume.
        2. Set auth.reject on volume for client1 using ip of client1.
        3. Set auth.allow on volume for client1 using ip of client1.
        4. Try to mount volume on client1. This should fail.
        5. Check the client1 log for AUTH_FAILED event.
        6. Mount volume on client2.This should fail.
        7. Check the client2 log for AUTH_FAILED event.
        8. Set auth.reject on volume for client1 using hostname of client1.
        9. Set auth.allow on volume for client1 using hostname of client1.
        10. Repeat steps 4 to 7
        """
        # Setting auth.reject on volume for client1 using ip
        auth_dict = {'all': [self.client_list[0]]}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Setting auth.allow on volume for client1 using ip
        auth_dict = {'all': [self.client_list[0]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount volume on client1
        redant.unauthenticated_mount(self.vol_name, self.server_list[0],
                                     self.mountpoint, self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        prev_log_statement = redant.is_auth_failure(self.client_list[0])

        # Mounting volume on client2
        redant.unauthenticated_mount(self.vol_name, self.server_list[0],
                                     self.mountpoint, self.client_list[1])

        # Obtain hostname of client1
        ret = redant.execute_abstract_op_node("hostname", self.client_list[0])
        hostname_client1 = ret['msg'][0].rstrip('\n')

        # Setting auth.reject on volume for client1 using hostname
        auth_dict = {'all': [hostname_client1]}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Setting auth.allow on volume for client1 using hostname
        auth_dict = {'all': [hostname_client1]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount volume on client1
        redant.unauthenticated_mount(self.vol_name, self.server_list[0],
                                     self.mountpoint, self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        redant.is_auth_failure(self.client_list[0], prev_log_statement)

        # Mounting volume on client2
        redant.unauthenticated_mount(self.vol_name, self.server_list[0],
                                     self.mountpoint, self.client_list[1])

        # Verify whether mount failure on client2 is due to auth error
        redant.is_auth_failure(self.client_list[1], prev_log_statement)
