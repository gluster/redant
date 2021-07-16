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
    TC to verify the precedence of auth.reject option over auth.allow option.
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
from tests.d_parent_test import DParentTest


class TestVerifyAuthRejectPrecedence(DParentTest):

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
        This testcase verifies the precedence of auth.reject volume option
        over auth.allow volume option.
        Verification will be done in volume level and sub-directory level
        using both IP and hostname.
        Steps:
        1. Create and start volume.
        2. Mount volume on client1.
        3. Create directory d1 on client1 mountpoint.
        4. Unmount volume from client1.
        5. Set auth.reject on volume for all clients(*).
        6. Set auth.allow on volume for client1 and client2 using ip.
        7. Try to mount volume on client1. This should fail.
        8. Check the client1 log for AUTH_FAILED event.
        9. Try to mount volume on client2. This should fail.
        10. Check the client2 log for AUTH_FAILED event.
        11. Set auth.allow on volume for client1 and client2 using hostname.
        12. Repeat steps 7 to 10.
        13. Set auth.reject on sub-directory d1 for all clients(*).
        14. Set auth.allow on sub-directory d1 for client1 and client2 using
            ip.
        15. Try to mount d1 on client1. This should fail.
        16. Check the client1 log for AUTH_FAILED event.
        17. Try to mount d1 on client2. This should fail.
        18. Check the client2 log for AUTH_FAILED event.
        19. Set auth.allow on sub-directory d1 for client1 and client2 using
            hostname.
        20. Repeat steps 15 to 18.
        """
        # Mounting volume on client2
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Creating sub directory d1 on mounted volume
        redant.create_dir(self.mountpoint, "d1", self.client_list[0])

        # Unmount volume from client1
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])

        # Setting auth.reject on volume for all clients
        auth_dict = {'all': ['*']}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Setting auth.allow on volume for client1 and client2 using ip
        auth_dict = {'all': [self.client_list[0], self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount volume on client1
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        prev_log_statement_c1 = redant.is_auth_failure(self.client_list[0])

        # Trying to mount volume on client2
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[1])

        # Verify whether mount failure on client2 is due to auth error
        prev_log_statement_c2 = redant.is_auth_failure(self.client_list[1])

        # Obtain hostname of client1
        ret = redant.execute_abstract_op_node("hostname", self.client_list[0])
        hostname_client1 = ret['msg'][0].rstrip('\n')

        # Obtain hostname of client2
        ret = redant.execute_abstract_op_node("hostname", self.client_list[1])
        hostname_client2 = ret['msg'][0].rstrip('\n')

        # Setting auth.allow on volume for client1 and client2 using hostname
        auth_dict = {'all': [hostname_client1, hostname_client2]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount volume on client1
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        prev_log_statement_c1 = redant.is_auth_failure(self.client_list[0],
                                                       prev_log_statement_c1)

        # Trying to mount volume on client2
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[1])

        # Verify whether mount failure on client2 is due to auth error
        prev_log_statement_c2 = redant.is_auth_failure(self.client_list[1],
                                                       prev_log_statement_c2)

        # Setting auth.reject on d1 for all clients
        auth_dict = {'/d1': ['*']}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Setting auth.allow on d1 for client1 and client2 using ip
        auth_dict = {'/d1': [self.client_list[0], self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount d1 on client1
        subdir_volume_client1 = f"{self.vol_name}/d1"
        redant.unauthenticated_mount(subdir_volume_client1,
                                     self.server_list[0], self.mountpoint,
                                     self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        prev_log_statement_c1 = redant.is_auth_failure(self.client_list[0],
                                                       prev_log_statement_c1)

        # Trying to mount d1 on client2
        subdir_volume_client2 = f"{self.vol_name}/d1"
        redant.unauthenticated_mount(subdir_volume_client2,
                                     self.server_list[0], self.mountpoint,
                                     self.client_list[1])

        # Verify whether mount failure on client2 is due to auth error
        prev_log_statement_c2 = redant.is_auth_failure(self.client_list[1],
                                                       prev_log_statement_c2)

        # Setting auth.allow on d1 for client1 and client2 using hostname
        auth_dict = {'/d1': [hostname_client1, hostname_client2]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount d1 on client1
        redant.unauthenticated_mount(subdir_volume_client1,
                                     self.server_list[0], self.mountpoint,
                                     self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        redant.is_auth_failure(self.client_list[0], prev_log_statement_c1)

        # Trying to mount d1 on client2
        redant.unauthenticated_mount(subdir_volume_client2,
                                     self.server_list[0], self.mountpoint,
                                     self.client_list[1])

        # Verify whether mount failure on client2 is due to auth error
        redant.is_auth_failure(self.client_list[1], prev_log_statement_c2)
