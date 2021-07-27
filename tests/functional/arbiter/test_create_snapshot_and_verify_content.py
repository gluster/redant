"""
 Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to verify content on creating snapshots
"""

# disruptive;arb,dist-arb
# TODO: nfs
from tests.d_parent_test import DParentTest


class TestArbiterSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        - Create an arbiter volume
        - Create IO
        - Calculate arequal of the mount point
        - Take a snapshot of the volume
        - Create new data on mount point
        - Restore the snapshot
        - Calculate arequal of the mount point
        - Compare arequals
        """
        # Creating files on client side
        proc = redant.create_deep_dirs_with_files(self.mountpoint, 1, 2, 2,
                                                  2, 20, self.client_list[0])

        mount_dict = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Get arequal before snapshot
        arequal_before_snapshot = redant.collect_mounts_arequal(mount_dict)

        # Create snapshot
        snapshot_name = 'testsnap'
        redant.snap_create(self.vol_name, snapshot_name, self.server_list[0])

        # Add files on client side
        proc = redant.create_deep_dirs_with_files(self.mountpoint, 1, 2, 2,
                                                  2, 20, self.client_list[0])
        ret = redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Stop the volume
        redant.volume_stop(self.vol_name, self.server_list[0])

        # Revert snapshot
        redant.snap_restore(snapshot_name, self.server_list[0])

        # Start the volume
        redant.volume_start(self.vol_name, self.server_list[0])

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Get arequal after restoring snapshot
        arequal_after_restoring = redant.collect_mounts_arequal(mount_dict)

        # Checking arequals before creating and after restoring snapshot
        if arequal_before_snapshot != arequal_after_restoring:
            raise Exception("Arequal before creating snapshot "
                            "and after restoring snapshot are not equal")
