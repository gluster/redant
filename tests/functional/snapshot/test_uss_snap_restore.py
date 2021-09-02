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
    TC will validate USS after Snapshot restore. The restored snapshot
    should not be listed under the '.snaps' directory.
"""

# disruptive;rep,dist-rep,disp,dist,dist-disp
# TODO: NFS
from tests.d_parent_test import DParentTest


class TestUssSnapRestore(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        * Perform I/O on mounts
        * Enable USS on volume
        * Validate USS is enabled
        * Create a snapshot
        * Activate the snapshot
        * Perform some more I/O
        * Create another snapshot
        * Activate the second
        * Restore volume to the second snapshot
        * From mount point validate under .snaps
          - first snapshot should be listed
          - second snapshot should not be listed
        """
        self.snapshots = [(f'snap-{i}') for i in range(0, 2)]
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Perform I/O
        self.all_mounts_procs = []
        proc = redant.create_files('1k', self.mountpoint, self.client_list[0],
                                   10, 'firstfiles')
        self.all_mounts_procs.append(proc)

        # Wait for IO to complete and validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Get stat of all the files/dirs created.
        ret = redant.get_mounts_stat(self.mounts)
        if not ret:
            raise Exception("Stat failed on some of the clients")

        # Enable USS
        redant.enable_uss(self.vol_name, self.server_list[0])

        # Validate USS is enabled
        ret = redant.is_uss_enabled(self.vol_name, self.server_list[0])
        if not ret:
            raise Exception(f"USS is disabled on volume {self.vol_name}")

        # Create a snapshot
        redant.snap_create(self.vol_name, self.snapshots[0],
                           self.server_list[0])

        # Check for number of snaps using snap_list it should be 1 now
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 1:
            raise Exception("Number of snaps not consistent "
                            f"for volume {self.vol_name}")

        # Activate the snapshot
        redant.snap_activate(self.snapshots[0], self.server_list[0])

        # Perform I/O
        self.all_mounts_procs = []
        proc = redant.create_files('1k', self.mountpoint, self.client_list[0],
                                   10, 'secondfiles')
        self.all_mounts_procs.append(proc)

        # Wait for IO to complete and validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Get stat of all the files/dirs created.
        ret = redant.get_mounts_stat(self.mounts)
        if not ret:
            raise Exception("Stat failed on some of the clients")

        # Create another snapshot
        redant.snap_create(self.vol_name, self.snapshots[1],
                           self.server_list[0])

        # Check for number of snaps using snap_list it should be 2 now
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 2:
            raise Exception("Number of snaps not consistent "
                            f"for volume {self.vol_name}")

        # Activate the second snapshot
        redant.snap_activate(self.snapshots[1], self.server_list[0])

        # Restore volume to the second snapshot
        ret = redant.snap_restore_complete(self.vol_name, self.snapshots[1],
                                           self.server_list[0])
        if not ret:
            raise Exception(f"Failed to restore snapshot {self.snapshots[1]}")

        # Verify all volume processes are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("Few process after volume start are offline for "
                            f"volume: {self.vol_name}")

        # Check snapd is running
        ret = redant.is_snapd_running(self.vol_name, self.server_list[0])
        if not ret:
            raise Exception("Failed: snapd is not running for volume "
                            f"{self.vol_name}")

        # List activated snapshots under the .snaps directory
        ret = redant.uss_list_snaps(self.client_list[0], self.mountpoint,
                                    recursive=False)
        snap_dir_list = "".join(ret['msg']).strip().split('\n')
        if not snap_dir_list:
            raise Exception("Failed to list snapshots under .snaps directory")

        # Check for first snapshot as it should get listed here
        if self.snapshots[0] not in snap_dir_list:
            raise Exception(f"Unexpected : {self.snapshots[0]} not listed "
                            "under .snaps directory")

        # Check for second snapshot as it should not get listed here
        if self.snapshots[1] in snap_dir_list:
            raise Exception(f"Unexpected : {self.snapshots[1]} listed "
                            "under .snaps directory")
