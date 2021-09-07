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
    This test case validates fuse subdir functionality when remove-brick
    operation is performed
"""

# disruptive;dist,dist-rep,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestSubdirWithRemoveBrick(DParentTest):

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
        - Create 2 subdir on client subdir1 and subdir2
        - Auth allow - Client1(subdir1,subdir2),Client2(subdir1,subdir2)
        - Mount the subdir to their respective clients
        - Start IO's on both subdirs
        - Perform remove-brick
        - Validate on client if subdir's are mounted post remove-brick
          operation is performed
        """
        self.is_mounted = False

        # Create  directories subdir1 and subdir2 on mount point
        redant.create_dir(self.mountpoint, "subdir1", self.client_list[0])
        redant.create_dir(self.mountpoint, "subdir2", self.client_list[1])

        # unmount volume
        for client in self.client_list[0:2]:
            redant.volume_unmount(self.vol_name, self.mountpoint, client)

        # Set authentication on the subdirectory subdir1
        # and subdir2 to access by 2 clients
        auth_dict = {'/subdir1': [self.client_list[0], self.client_list[1]],
                     '/subdir2': [self.client_list[0], self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mount Subdir1 mount on client 1 and check if it is mounted properly
        volname = f"{self.vol_name}/subdir1"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Mount Subdir2 mount on client 2 and check if it is mounted properly
        volname = f"{self.vol_name}/subdir2"
        redant.authenticated_mount(volname, self.server_list[0],
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

        # Perform remove brick operation when subdir is mounted on client
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   rebal_timeout=600)
        if not ret:
            raise Exception("Remove brick operation failed on "
                            f"{self.vol_name}")

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")

        # Log Volume Info and Status after performing remove brick
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.volname}")

        # Again Checking subdir1 is mounted or not on Client 1
        volname = f"{self.vol_name}/subdir1"
        ret = redant.is_mounted(volname, self.mountpoint, self.client_list[0],
                                self.server_list[0])
        if not ret:
            raise Exception("Volume not mounted on mount point: "
                            f"{self.mountpoint}")

        # Again Checking subdir2 is mounted or not on Client 2
        volname = f"{self.vol_name}/subdir2"
        ret = redant.is_mounted(volname, self.mountpoint, self.client_list[1],
                                self.server_list[0])
        if not ret:
            raise Exception("Volume not mounted on mount point: "
                            f"{self.mountpoint}")
