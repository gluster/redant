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
    Test Cases in this module tests the creation of clone from snapshot of
    volume and delete snapshot and original volume.
    Validate cloned volume is not affected.
"""

# disruptive;rep,dist,disp,dist-rep,dist-disp
from time import sleep
from tests.d_parent_test import DParentTest


class TestSnapshotSelfheal(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. Create and mount distributed-replicated volume
        2. Perform I/O on mountpoints
        3. Create snapshot
        4. activate snapshot created in step3
        5. clone created snapshot in step3
        6. delete original volume
        7. Validate clone volume
        """
        self.clone = "clone1"
        self.mpoint = "/mnt/clone1"
        self.snap = "snap1"

        # Perform I/O
        all_mounts_procs = []
        self.mounts = [{
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }]

        # Create files
        for mount_obj in self.mounts:
            proc = redant.create_files('1k', mount_obj['mountpath'],
                                       mount_obj['client'], 100)
            all_mounts_procs.append(proc)

        # Validate IO
        if not self.redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")

        # Creating snapshot
        redant.snap_create(self.vol_name, self.snap, self.server_list[0])

        # Activating snapshot
        redant.snap_activate(self.snap, self.server_list[0])

        # snapshot list
        ret = redant.snap_list(self.server_list[0])
        if self.snap not in ret['msg']['snapList']['snapshot']:
            raise Exception(f"Failed to validate snapshot {self.snap}"
                            " in snap list")

        # Creating a Clone of snapshot:
        redant.snap_clone(self.snap, self.clone, self.server_list[0])

        # After cloning a volume wait for 5 second to start the volume
        sleep(5)

        # Validate clone volumes are started
        redant.volume_start(self.clone, self.server_list[0])

        for mount_obj in self.mounts:
            # Unmount Volume
            redant.volume_unmount(self.vol_name, mount_obj['mountpath'],
                                  mount_obj['client'])

        # Delete original volume
        ret = redant.cleanup_volume(self.server_list[0], self.vol_name)
        if not ret:
            raise Exception(f"Failed to delete the volume: {self.vol_name}")

        # get volume info
        vol_info = redant.get_volume_info(self.server_list[0], self.clone)
        if not vol_info:
            raise Exception("Failed to get volume info "
                            f"for cloned volume {self.clone}")
        if vol_info[self.clone]['statusStr'] != 'Started':
            raise Exception("Unexpected: cloned volume is not started "
                            f"{self.clone}")

        # Volume status
        ret = redant.get_volume_status(self.clone, self.server_list[0])
        if not ret:
            raise Exception(f"Failed to get volume status for {self.clone}")

        if self.clone not in ret.keys():
            raise Exception("Failed to get volume status for volume "
                            f"{self.clone}")

        # Volume list validate
        ret = redant.get_volume_list(self.server_list[0])
        if self.clone not in ret:
            raise Exception("Failed to validate volume list for volume "
                            f" {self.clone}")
