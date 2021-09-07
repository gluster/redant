"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    This test case validates fuse subdir functionality when earlier
    exported subdir is renamed along with auth allow functionality
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestSubdirWithRename(DParentTest):

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

    def run_test(self, redant):
        """
        Steps:
        - Mount the volume
        - Create 1 subdir on mountpoint "d1"
        - Auth allow - Client1(d1),Client2(full volume)
        - Mount the subdir "d1" on client1 and volume on client2
        - Start IO's on all the mount points
        - Perform rename operation from client2.Rename the subdir
          "d1" to "d1_renamed"
        - unmount volume and subdir from clients
        - Try mounting "d1" on client 1.This should fail.
        - Try mounting "d1_renamed" on client 1.This should fail.
        - Again set authentication.Auth allow -
        - Client1(d1_renamed),Client2(full volume)
        - Mount "d1_renamed" on client1 and volume on client2
        """
        self.is_mounted = False

        # Create  directory d1 on mount point
        redant.create_dir(self.mountpoint, "d1", self.client_list[0])

        # unmount volume
        for client in self.client_list[0:2]:
            redant.volume_unmount(self.vol_name, self.mountpoint, client)

        # Set authentication on the subdirectoy "d1" to access by client1
        # and volume to access by client2
        auth_dict = {'/d1': [self.client_list[0]],
                     '/': [self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mount Subdirectory d1 on client 1 and volume on client 2
        volname = f"{self.vol_name}/d1"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[1])

        self.is_mounted = True

        # Start IO on all the subdir mounts.
        self.subdir_mounts = [{
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }, {
            "client": self.client_list[1],
            "mountpath": self.mountpoint
        }]
        self.all_mounts_procs = []
        count = 1
        for mount_obj in self.subdir_mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 3, 4, 4,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count = count + 10

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs,
                                       self.subdir_mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Get stat of all the files/dirs created.
        if not redant.get_mounts_stat(self.subdir_mounts):
            raise Exception("Stat on mountpoints failed.")

        # Rename the subdir "d1" to "d1_renamed" from client2
        source_fpath = f"{self.mountpoint}/d1"
        dest_fpath = f"{self.mountpoint}/d1_renamed"
        ret = redant.move_file(self.client_list[1], source_fpath,
                               dest_fpath)
        if not ret:
            raise Exception("Rename subdirectory failed")

        # unmount volume and subdir from clients
        redant.execute_abstract_op_node(f"umount {self.mountpoint}",
                                        self.client_list[0])
        redant.execute_abstract_op_node(f"umount {self.mountpoint}",
                                        self.client_list[1])
        self.is_mounted = False

        # Try mounting subdir "d1" on client1
        volname = f"{self.vol_name}/d1"
        redant.unauthenticated_mount(volname, self.server_list[0],
                                     self.mountpoint, self.client_list[0])

        # Try mounting subdir "d1_renamed" on client1
        volname = f"{self.vol_name}/d1_renamed"
        redant.unauthenticated_mount(volname, self.server_list[0],
                                     self.mountpoint, self.client_list[0])

        # Set authentication on the subdirectoy "d1_renamed" to access
        # by client1 and volume to access by client2
        auth_dict = {'/d1_renamed': [self.client_list[0]],
                     '/': [self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mount Subdirectory d1_renamed on client 1 and volume on client 2
        volname = f"{self.vol_name}/d1_renamed"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_mounted = True

        # Get stat of all the files/dirs created from both clients.
        if not redant.get_mounts_stat(self.subdir_mounts):
            raise Exception("Stat on mountpoints failed.")
