"""
 Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

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
    TC to check lookup and move operations on ec volume
"""

# disruptive;disp,dist-disp
# TODO: NFS
from random import sample
import traceback
from tests.d_parent_test import DParentTest


class TestEcLookupAndMoveOperations(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.mount_procs, self.mounts)):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.is_io_running = False
        # Check for 3 clients in the cluster
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=3)

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 self.vol_type_inf[self.volume_type],
                                 self.server_list, self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

    def _run_create_files(self, file_count, base_name, mpoint, client):
        """Run create files using file_dir_op.py"""
        proc = self.redant.create_files('1k', mpoint, client, file_count,
                                        base_name)
        self.mount_procs.append(proc)

    def run_test(self, redant):
        """
        Test Steps:
        1. Create volume and mount the volume on 3 clients, c1(client1),
           c2(client2), and, c3(client3)
        2. On c1, mkdir /c1/dir
        3. On c2, Create 4000 files on mount point i.e. "/"
        4. After step 3, Create next 4000 files on c2 on mount point i.e. "/"
        5. On c1 Create 10000 files on /dir/
        6. On c3 start moving 4000 files created on step 3 from mount point
            to /dir/
        7. On c3, start ls in a loop for 20 iterations
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Create directory on client2
        dir_on_mount = f"{self.mountpoint}/dir"
        redant.create_dir(self.mountpoint, "dir", self.mounts[1]['client'])

        # Create 4000 files on the mountpoint of client1
        proc = self.redant.create_files('10k', self.mounts[0]['mountpath'],
                                        self.mounts[0]['client'], 4000,
                                        "file_from_client1")
        if not redant.validate_io_procs(proc, self.mounts[0]):
            raise Exception("Failed to create files on client2")

        # Next IO to be ran in the background so using mount_procs list
        self.mount_procs = []
        # Create 4000 files from client 1
        self._run_create_files(file_count=4000,
                               base_name="files_on_client1_background_",
                               mpoint=self.mounts[0]['mountpath'],
                               client=self.mounts[0]['client'])
        self.is_io_running = True

        # Create next 10000 files on dir1 of client2
        self._run_create_files(file_count=10000,
                               base_name="files_on_client2_background_",
                               mpoint=dir_on_mount,
                               client=self.mounts[1]['client'])

        # Move the files created on client1 to dir from client3
        cmd = (f"for i in `seq 0 3999`; do mv {self.mounts[0]['mountpath']}"
               f"/file_from_client1_$i.txt {dir_on_mount}; ")
        proc = redant.execute_command_async(cmd, self.mounts[2]['mountpath'])
        self.mount_procs.append(proc)

        # Perform a lookup in loop from client3 for 20 iterations
        cmd = f"ls -R {self.mounts[2]['mountpath']}"
        counter = 20
        while counter:
            redant.execute_abstract_op_node(cmd, self.mounts[2]['client'])
            counter -= 1

        if not redant.validate_io_procs(self.mount_procs, self.mounts):
            raise Exception("IO failed on the clients")
        self.is_io_running = False

        # Clear out the mountpoints on the client
        for mount_obj in self.mounts:
            cmd = f"rm -rf {mount_obj['mountpath']}/*"
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

        # Test2: test_ec_lookup_and_move_operations_few_bricks_are_offline
        """
        Test Steps:
        1. Mount this volume on 3 mount point, c1, c2, and c3
        2. Bring down two bricks offline in each subvol.
        3. On client1: under dir1 create files f{1..10000} run in background
        4. On client2: under root dir of mountpoint touch x{1..1000}
        5. On client3: after step 4 action completed, start creating
           x{1001..10000}
        6. Bring bricks online which were offline(brought up all the bricks
           which were down (2 in each of the two subvols)
        7. While IO on Client1 and Client3 were happening, On client2 move all
           the x* files into dir1
        8. Perform lookup from client 3
        """
        # List two bricks in each subvol
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed ot get the volume subvols")

        bricks_to_bring_offline = []
        for subvol in subvols:
            bricks_to_bring_offline.extend(sample(subvol, 2))

        # Bring two bricks of each subvol offline
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)

        # Validating the bricks are offline or not
        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception("Few of the bricks are still online in"
                            f" {bricks_to_bring_offline}")

        # Create directory on client1
        dir_on_mount = f"{self.mountpoint}/dir"
        redant.create_dir(self.mountpoint, "dir", self.mounts[0]['client'])

        # Next IO to be ran in the background so using mount_procs
        # and run_async.
        self.mount_procs = []

        # On client1: under dir1 create files f{1..10000} run in background
        self._run_create_files(file_count=10000,
                               base_name="f_",
                               mpoint=dir_on_mount,
                               client=self.mounts[0]['client'])
        self.is_io_running = True

        # On client3: under root dir of the mountpoint touch x{1..1000}
        proc = redant.create_files('10k', self.mounts[2]['mountpath'],
                                   self.mounts[2]['client'], 1000, 'x')
        if not redant.validate_io_procs(proc, self.mounts[2]):
            raise Exception("File creation failed")

        # On client2: start creating x{1001..10000}
        cmd = (f"cd {self.mounts[1]['mountpath']}; for i in `seq 1000 10000`"
               "; do touch x$i; done;")
        proc = redant.execute_command_async(cmd, self.mounts[1]['client'])
        self.mount_procs.append(proc)

        # Bring bricks online with volume start force
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Check whether bricks are online or not
        if not redant.are_bricks_online(self.vol_name,
                                        bricks_to_bring_offline,
                                        self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} are still "
                            "offline")

        # From client3 move all the files with name starting with x into dir1
        cmd = (f"for i in `seq 0 999`; do mv {self.mounts[2]['mountpath']}"
               f"/x$i.txt {dir_on_mount}; done")
        proc = redant.execute_command_async(cmd, self.mounts[2]['client'])
        self.mount_procs.append(proc)

        # Perform a lookup in loop from client3 for 20 iterations
        cmd = f"ls -R {self.mounts[2]['mountpath']}"
        counter = 20
        while counter:
            redant.execute_abstract_op_node(cmd, self.mounts[2]['client'])
            counter -= 1

        if not redant.validate_io_procs(self.mount_procs, self.mounts):
            raise Exception("IO failed on the clients")
        self.is_io_running = False

        # Wait for heal to complete
        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name):
            raise Exception("Heal is not yet completed")
