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
    Test Cases in this module tests the volume stop, start, reset
    operations when sub-dirs are mounted
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestVolumeSetOpsSubDirsMounted(DParentTest):

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
        1. Create two sub-directories on mounted volume.
        2. Unmount volume from clients.
        3. Mount each sub-directory to two different clients.
        4. Perform IO on mounts.
        5. Perform volume stop operation.
        6. Perform volume start operation.
        7. Perform volume reset operation.
        """
        self.is_mounted = False
        # Creating two sub directories on mounted volume
        redant.create_dir(self.mountpoint, "d1", self.client_list[0])
        redant.create_dir(self.mountpoint, "d2", self.client_list[1])

        # Unmounting volumes
        for client in self.client_list:
            redant.volume_unmount(self.vol_name, self.mountpoint, client)

        # Mounting one sub directory on each client.
        volname = f"{self.vol_name}/d1"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])
        volname = f"{self.vol_name}/d2"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[1])
        self.is_mounted = True

        # Start IO on all mounts.
        self.subdir_mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        all_mounts_procs = []
        count = 1
        for mount_obj in self.subdir_mounts[0:2]:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 3, 4, 4,
                                                      mount_obj['client'])
            all_mounts_procs.append(proc)
            count = count + 10

        # Validate IO
        ret = redant.validate_io_procs(all_mounts_procs,
                                       self.subdir_mounts[0:2])
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Get stat of all the files/dirs created.
        if not redant.get_mounts_stat(self.subdir_mounts[0:2]):
            raise Exception("Stat on mountpoints failed.")

        # Stop volume
        redant.volume_stop(self.vol_name, self.server_list[0])

        # Start volume
        redant.volume_start(self.vol_name, self.server_list[0])

        # Reset volume
        redant.volume_reset(self.vol_name, self.server_list[0])
