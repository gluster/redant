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
    TC to check the authentication allow feature
    using auth.allow and auth.reject volume options
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestFuseAuthRejectAllow(DParentTest):

    def terminate(self):
        """
        Unmount the volume if still mounted
        """
        try:
            if self.is_vol_mounted:
                cmd = f"umount {self.mountpoint}"
                for client in self.client_list:
                    self.redant.execute_abstract_op_node(cmd, client, False)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

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
        Verify auth.reject and auth.allow volume options in volume level using
        both client ip and hostname.
        Verify auth.reject and auth.allow volume options in sub-directory
        level using both client ip and hostname.
        Steps:
        1. Create and start volume.
        2. Set auth.reject on volume for client1 using ip of client1.
        3. Set auth.allow on volume for client2 using ip of client2.
        4. Try to mount volume on client1. This should fail.
        5. Check the client1 log for AUTH_FAILED event.
        6. Mount volume on client2.
        7. Unmount the volume from client2.
        8. Set auth.reject on volume for client1 using hostname of client1.
        9. Set auth.allow on volume for client2 using hostname of client2.
        10. Repeat steps 4 to 6
        11. Create directory d1 on client2 mountpoint.
        12. Unmount the volume from client2.
        13. Set auth.reject on d1 for client1 using ip of client1.
        14. Set auth.allow on d1 for client2 using ip of client2.
        15. Try to mount d1 on client1. This should fail.
        16. Check the client1 log for AUTH_FAILED event.
        17. Mount d1 on client2.
        18. Unmount d1 from client2.
        19. Set auth.reject on d1 for client1 using hostname of client1.
        20. Set auth.allow on d1 for client2 using hostname of client2.
        21. Repeat steps 15 to 18.
        """
        self.is_vol_mounted = False
        # Setting auth.reject on volume for client1 using ip
        auth_dict = {'all': [self.client_list[0]]}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Setting auth.allow on volume for client2 using ip
        auth_dict = {'all': [self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount volume on client1
        redant.unauthenticated_mount(self.vol_name, self.server_list[0],
                                     self.mountpoint, self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        prev_log_statement = redant.is_auth_failure(self.client_list[0])

        # Mounting volume on client2
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_vol_mounted = True

        # Unmount volume from client2
        cmd = f"umount {self.mountpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[1])
        self.is_vol_mounted = False

        # Obtain hostname of client1
        ret = redant.execute_abstract_op_node("hostname", self.client_list[0])
        hostname_client1 = ret['msg'][0].rstrip('\n')

        # Obtain hostname of client2
        ret = redant.execute_abstract_op_node("hostname", self.client_list[1])
        hostname_client2 = ret['msg'][0].rstrip('\n')

        # Setting auth.reject on volume for client1 using hostname
        auth_dict = {'all': [hostname_client1]}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Setting auth.allow on volume for client2 using hostname
        auth_dict = {'all': [hostname_client2]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount volume on client1
        redant.unauthenticated_mount(self.vol_name, self.server_list[0],
                                     self.mountpoint, self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        prev_log_statement = redant.is_auth_failure(self.client_list[0],
                                                    prev_log_statement)

        # Mounting volume on client2
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_vol_mounted = True

        # Creating sub directory d1 on mounted volume
        redant.create_dir(self.mountpoint, "d1", self.client_list[1])

        # Unmount volume from client2
        cmd = f"umount {self.mountpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[1])
        self.is_vol_mounted = False

        # Setting auth.reject on d1 for client1 using ip
        auth_dict = {'/d1': [self.client_list[0]]}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Setting auth.allow on d1 for client2 using ip
        auth_dict = {'/d1': [self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount d1 on client1
        self.subdir_vol = f"{self.vol_name}/d1"
        subdir_volume_client1 = f"{self.vol_name}/d1"
        redant.unauthenticated_mount(subdir_volume_client1,
                                     self.server_list[0], self.mountpoint,
                                     self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        prev_log_statement = redant.is_auth_failure(self.client_list[0],
                                                    prev_log_statement)

        # Mounting d1 on client2
        subdir_volume_client2 = f"{self.vol_name}/d1"
        redant.authenticated_mount(subdir_volume_client2, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_vol_mounted = True

        # Unmount d1 from client2
        cmd = f"umount {self.mountpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[1])
        self.is_vol_mounted = False

        # Setting auth.reject on d1 for client1 using hostname
        auth_dict = {'/d1': [hostname_client1]}
        if not redant.set_auth_reject(self.vol_name, self.server_list[0],
                                      auth_dict):
            raise Exception("Failed to set authentication")

        # Setting auth.allow on d1 for client2 using hostname
        auth_dict = {'/d1': [hostname_client2]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Trying to mount d1 on client1
        redant.unauthenticated_mount(subdir_volume_client1,
                                     self.server_list[0], self.mountpoint,
                                     self.client_list[0])

        # Verify whether mount failure on client1 is due to auth error
        redant.is_auth_failure(self.client_list[0], prev_log_statement)

        # Mounting d1 on client2
        redant.authenticated_mount(subdir_volume_client2, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_vol_mounted = True

        # Unmount d1 from client2
        cmd = f"umount {self.mountpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[1])
        self.is_vol_mounted = False
