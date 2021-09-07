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
        Test Cases in this module tests the Fuse sub directory feature
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    Tests to verify auth.allow using fqdn on Fuse subdir feature
    """
    def _mount_and_verify(self, subdir, client):
        # Trying to mount volume sub directories on unauthenticated clients
        cmd = (f"mount.glusterfs {self.server_list[0]}:/{subdir} \
               {self.mountpoint}")
        self.redant.execute_abstract_op_node(cmd, client, False)
        cmd = f"mount | grep {subdir}"
        ret = self.redant.execute_abstract_op_node(cmd, client, False)
        if ret['error_code'] == 0:
            raise Exception("Mount operation did not fail as expected")

    def run_test(self, redant):
        """
        Check sub dir auth.allow functionality using FQDN

        Steps:
        1. Create two sub directories on mounted volume
        2. Unmount volume from clients
        3. Set auth.allow on sub dir d1 for client1 and d2 for client2 using
           fqdn
        4. Mount d1 on client1 and d2 on client2. This should pass.
        5. Try to mount d1 on client2 and d2 on client1. This should fail.
        """
        # Check client requirements
        redant.check_hardware_requirements(clients=self.client_list,
                                           clients_count=2)

        # Creating sub directories on mounted volume
        redant.create_dir(self.mountpoint, 'd1', self.client_list[0])
        redant.create_dir(self.mountpoint, 'd2', self.client_list[0])

        # Unmounting volumes
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[1])

        # Obtain hostname of clients
        ret = redant.execute_abstract_op_node("hostname", self.client_list[0])
        hostname_client1 = ret['msg'][0].rstrip('\n')

        ret = redant.execute_abstract_op_node("hostname", self.client_list[1])
        hostname_client2 = ret['msg'][0].rstrip('\n')

        # Setting authentication
        auth_dict = {'/d1': [hostname_client1],
                     '/d2': [hostname_client2]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Creating mounts list for authenticated clients
        subdir_mount1 = f"{self.vol_name}/d1"
        subdir_mount2 = f"{self.vol_name}/d2"

        # Mounting sub directories on authenticated clients
        redant.authenticated_mount(subdir_mount1, self.server_list[0],
                                   self.mountpoint, self.client_list[0])
        redant.authenticated_mount(subdir_mount2, self.server_list[0],
                                   self.mountpoint, self.client_list[1])

        # Trying to mount volume sub directories on unauthenticated clients
        self._mount_and_verify(subdir_mount2, self.client_list[0])
        self._mount_and_verify(subdir_mount1, self.client_list[1])
