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
    Test case validates multiple dirs mapping to multiple client
    having access to mount respective dirs,with auth allow functionality
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestMultipleDirMappingClient(DParentTest):

    def terminate(self):
        """
        Unmount the subdirs mounted in the TC
        """
        try:
            if self.is_mounted:
                cmd = f"umount {self.mountpoint}"
                for client in self.client_list[0:2]:
                    self.redant.execute_abstract_op_node(cmd, client, False)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    @DParentTest.setup_custom_enable
    def setup_test(self):
        # Check server requirements
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=2)

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
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def run_test(self, redant):
        """
        Mount the volume on client
        Create 2 subdir on client subdir1,subdir2
        Auth allow - Client1(subdir1),Client2(subdir2)
        Mount subdir1 on client1.Try Mounting subdir1 on client2
        Mount subdir2 on client2.Try Mounting subdir2 on client1
        """
        self.is_mounted = False

        # Creating two sub directories
        redant.create_dir(self.mountpoint, "dir1", self.client_list[0])
        redant.create_dir(self.mountpoint, "dir2", self.client_list[0])

        # Unmounting volumes
        for client in self.client_list:
            redant.volume_unmount(self.vol_name, self.mountpoint, client)

        # Set auth allow permission on subdirs
        auth_dict = {'/dir1': [self.client_list[0]],
                     '/dir2': [self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Test Subdir2 mount on client 1
        volname = f"{self.vol_name}/dir2"
        redant.unauthenticated_mount(volname, self.server_list[0],
                                     self.mountpoint, self.client_list[0])

        # Test Subdir1 mount on client 1
        volname = f"{self.vol_name}/dir1"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Test Subdir1 mount on client 2
        volname = f"{self.vol_name}/dir1"
        redant.unauthenticated_mount(volname, self.server_list[0],
                                     self.mountpoint, self.client_list[1])
        # Test Subdir2 mount on client 2
        volname = f"{self.vol_name}/dir2"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_mounted = True
