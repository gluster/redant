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
        Test cases in this module tests mount operation on clients having
        authentication to mount using combination of  FQDN and IP address.
"""
# disruptive;dist,rep,dist-rep,disp,dist-disp

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    Tests to verify authentication feature on fuse mount using a combination
    of IP and fqdn.
    """
    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Create and start the volume
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)

    def terminate(self):
        """
        Unmount the subdirs mounted in the TC
        """
        try:
            if self.is_mounted:
                cmd = f"umount {self.mountpoint}"
                for client in self.client_list:
                    self.redant.execute_abstract_op_node(cmd, client, False)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Verify auth.allow feature using a combination of client ip and fqdn.
        Steps:
        1. Setup and start volume
        2. Set auth.allow on volume using ip of client1 and hostname of
           client2.
        3. Mount the volume on client1 and client2.
        5. Create directory d1 on client1 mountpoint.
        6. Unmount the volume from client1 and client2.
        7. Set auth.allow on d1 using ip of client1 and hostname of client2.
        8. Mount d1 on client1 and client2.
        9. Unmount d1 from client1 and client2.
        """
        # Check client requirements
        redant.check_hardware_requirements(clients=self.client_list,
                                           clients_count=2)

        self.is_mounted = False
        # Obtain hostname of client2
        ret = redant.execute_abstract_op_node("hostname", self.client_list[1])
        hostname_client2 = ret['msg'][0].rstrip('\n')

        # Setting authentication on volume using ip of client1 and hostname of
        # client2.
        auth_dict = {'all': [self.client_list[0], hostname_client2]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mount volume on client1 and client2
        self.mountpoint = f"/mnt/{self.vol_name}"
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            redant.volume_mount(self.server_list[0],
                                self.vol_name,
                                self.mountpoint, client)

        # Creating directory d1 on mounted volume
        redant.create_dir(self.mountpoint, 'd1', self.client_list[0])

        # Unmount volume from client1 and client2
        for client in self.client_list:
            redant.volume_unmount(self.vol_name, self.mountpoint, client)

        # Setting authentication on d1 using ip of client1 and hostname of
        # client2.
        auth_dict = {'/d1': [self.client_list[0], hostname_client2]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        subdir_mount1 = f"{self.vol_name}/d1"

        # Mount sub-directory d1 on client1
        redant.authenticated_mount(subdir_mount1, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Mount sub-directory d1 on client2
        redant.authenticated_mount(subdir_mount1, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_mounted = True

        # Unmount sub-directory d1 from client1.
        redant.execute_abstract_op_node(f"umount {self.mountpoint}",
                                        self.client_list[0])

        # Unmount sub-directory d1 from client2.
        redant.execute_abstract_op_node(f"umount {self.mountpoint}",
                                        self.client_list[1])
        self.is_mounted = False
