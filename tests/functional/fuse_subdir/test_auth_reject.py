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
import traceback
from tests.d_parent_test import DParentTest


class TestFuseSubDirAuthReject(DParentTest):

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
        # Check client requirements
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

    def _mount_and_verify(self, volname, mountpoint, server, client):
        """
        Mount volume on client and verify that the mount failed
        """
        cmd = f"mount.glusterfs {server}:/{volname} {mountpoint}"
        self.redant.execute_abstract_op_node(cmd, client, False)
        cmd = f"mount | grep {volname}"
        ret = self.redant.execute_abstract_op_node(cmd, client, False)
        if ret['error_code'] == 0:
            raise Exception("Mount operation did not fail as expected")

    def run_test(self, redant):
        """
        Steps:
        1. Create two sub directories on mounted volume
        2. Unmount volume from clients
        3. Set auth.reject on sub dir d1 for client1 and d2 for client2
        4. Mount d2 on client1 and d1 on client2. This should pass.
        5. Try to mount d2 on client2 and d1 on client1. This should fail.
        """
        self.is_mounted = False

        # Create  directories subdir1 and subdir2 on mount point
        redant.create_dir(self.mountpoint, "d1", self.client_list[0])
        redant.create_dir(self.mountpoint, "d2", self.client_list[1])

        # Unmounting volumes
        for client in self.client_list[0:2]:
            redant.volume_unmount(self.vol_name, self.mountpoint, client)

        # Setting authentication (auth.reject) for directories
        auth_dict = {'/d1': [self.client_list[0]],
                     '/d2': [self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mounting sub directories on authenticated client
        volname = f"{self.vol_name}/d1"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        volname = f"{self.vol_name}/d2"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_mounted = True

        # Creating mountpoints for rejected client
        redant.create_dir("/mnt", "unauth_d2", self.client_list[0])
        redant.create_dir("/mnt", "unauth_d1", self.client_list[1])

        # Trying to mount sub directories on rejected client
        volname = f"{self.vol_name}/d1"
        mountpoint = "/mnt/unauth_d1"
        self._mount_and_verify(volname, mountpoint, self.server_list[0],
                               self.client_list[1])

        volname = f"{self.vol_name}/d2"
        mountpoint = "/mnt/unauth_d2"
        self._mount_and_verify(volname, mountpoint, self.server_list[0],
                               self.client_list[0])

        # Unmount sub directories
        redant.execute_abstract_op_node(f"umount {self.mountpoint}",
                                        self.client_list[0])
        redant.execute_abstract_op_node(f"umount {self.mountpoint}",
                                        self.client_list[1])
        self.is_mounted = False
