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
    Test case validates fuse subdir functionality when replace-brick
    operation is performed
 *Flaky Test*
 Reason: Heal doesn't complete
"""

# disruptive;disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestSubdirWithReplaceBrick(DParentTest):

    def terminate(self):
        """
        Unmount the subdirs mounted in the TC,
        and wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_mounted:
                cmd = f"umount {self.mountpoint}"
                for client in self.client_list[0:2]:
                    self.redant.execute_abstract_op_node(cmd, client, False)

            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.subdir_mounts)):
                    raise Exception("Failed to wait for IO to complete")

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
        - Mount the volume
        - Create 50 directories on mount point
        - Unmount volume
        - Auth allow - Client1(subdir25),Client2(subdir15)
        - Mount the subdir to their authorized respective clients
        - Start IO's on both subdirs
        - Perform replace-brick
        - Validate on client if subdir's are mounted post replace-brick
          operation is performed
        - Stat data on subdirs
        """
        self.is_mounted = False
        self.is_io_running = False

        # Create  directories on mount point
        for i in range(0, 50):
            redant.create_dir(self.mountpoint, f"subdir{i}",
                              self.client_list[0])

        # unmount volume
        for client in self.client_list:
            redant.volume_unmount(self.vol_name, self.mountpoint, client)

        # Set authentication on the subdirectory subdir25 to access by
        # client1 and subdir15 to access by 2 clients
        auth_dict = {'/subdir25': [self.client_list[0]],
                     '/subdir15': [self.client_list[1]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mount Subdirectory subdir25 on client 1 and subdir15 on client 2
        volname = f"{self.vol_name}/subdir25"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])
        volname = f"{self.vol_name}/subdir15"
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

        self.is_io_running = True

        # Get stat of all the files/dirs created.
        if not redant.get_mounts_stat(self.subdir_mounts):
            raise Exception("Stat on mountpoints failed.")

        # Log Volume Info and Status before replacing brick from the volume.
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.volname}")

        # Replace brick from a sub-volume
        sbrick = redant.get_all_bricks(self.vol_name, self.server_list[0])[0]
        sbrick_host, sbrick_root = sbrick.split(':')
        dbrick_root = sbrick_root[0:sbrick.split(':')[1].rfind("/")]
        dbrick = f"{sbrick_host}:{dbrick_root}/new_replaced_brick"
        ret = redant.replace_brick_from_volume(self.vol_name,
                                               self.server_list[0],
                                               self.server_list,
                                               sbrick, dbrick)
        if not ret:
            raise Exception("Failed to replace  brick from the volume")

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")

        # Log Volume Info and Status after replacing the brick
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.volname}")

        # Wait for self-heal to complete
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name,
                                              timeout_period=1800):
            raise Exception("Heal has not yet completed")

        # Again validate if subdirectories are still mounted post replace-brick
        volname = "subdir25"
        ret = redant.is_mounted(volname, self.mountpoint, self.client_list[0],
                                self.server_list[0])
        if not ret:
            raise Exception("Subdir not mounted after replace-brick")

        volname = "subdir15"
        ret = redant.is_mounted(volname, self.mountpoint, self.client_list[1],
                                self.server_list[0])
        if not ret:
            raise Exception("Subdir not mounted after replace-brick")

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs,
                                       self.subdir_mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")
        self.is_io_running = False
