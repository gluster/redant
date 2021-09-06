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
    Test case validates one level below subdir mount functionality.
    Different clients for parent dir and child dirs,with
    auth allow functionality
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestSubdirLevelDownDirMapping(DParentTest):

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
        Steps:
        - Mount the volume on client
        - Create nested dir -p parentDir/childDir on mount point
        - Auth allow - Client1(parentDir),Client2(parentDir/childDir)
        - Mount parentDir on client1.Try Mounting parentDir/childDir on client2
        - Mount parentDir/childDir on client2.Try Mounting parentDir on client1
        """
        self.is_mounted = False

        # Create nested subdirectories
        redant.create_dir(self.mountpoint, "parentDir/childDir",
                          self.client_list[0])

        # unmount volume
        for client in self.client_list:
            redant.volume_unmount(self.vol_name, self.mountpoint, client)

        # Set auth allow permission on subdirs
        auth_dict = {'/parentDir': [self.client_list[0]],
                     '/parentDir/childDir': [self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Test Subdir2 mount on client 1
        volname = f"{self.vol_name}/parentDir/childDir"
        redant.unauthenticated_mount(volname, self.server_list[0],
                                     self.mountpoint, self.client_list[0])

        # Test Subdir1 mount on client 1
        volname = f"{self.vol_name}/parentDir"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Test Subdir1 mount on client 2
        volname = f"{self.vol_name}/parentDir"
        redant.unauthenticated_mount(volname, self.server_list[0],
                                     self.mountpoint, self.client_list[1])

        # Test Subdir2 mount on client 2
        volname = f"{self.vol_name}/parentDir/childDir"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_mounted = True
