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
    one volume.
"""

# disruptive;dist,dist-rep
from time import sleep
from tests.d_parent_test import DParentTest


class TestSnapshotRebalance(DParentTest):

    def _check_arequal(self):
        """
        Check arequals for the bricks
        """
        # Get the subvolumes
        subvols = self.redant.get_subvols(self.clone1, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols for the volume")
        num_subvols = len(subvols)

        # Get arequals and compare
        for i in range(0, num_subvols):
            # Get arequal for first brick
            arequal = self.redant.collect_bricks_arequal(subvols[i][0])
            first_brick_total = arequal[0][-1].split(':')[-1]

            # Get arequal for every brick and compare with first brick
            arequals = self.redant.collect_bricks_arequal(subvols[i])
            for arequal in arequals:
                brick_total = arequal[-1].split(':')[-1]
                if first_brick_total != brick_total:
                    raise Exception('Arequals for subvol and brick are '
                                    'not equal')

    def run_test(self, redant):
        """
        Steps:
        1. Create snapshot of a volume
        2. Activate snapshot
        3. Clone snapshot and Activate
        4. Mount Cloned volume
        5. Perform I/O on mount point
        6. Calculate arequal for bricks and mountpoints
        7. Add-brick more brick to cloned volume
        8. Initiate Re-balance
        9. validate areequal of bricks and mountpoints
        """
        self.snap = "snap0"
        self.clone = "clone1"
        self.mount1 = "/mnt/clone1"

        # Creating snapshot:
        redant.snap_create(self.vol_name, self.snap, self.server_list[0])

        # Activating snapshot
        redant.snap_activate(self.snap, self.server_list[0])

        # Creating a Clone of snapshot:
        redant.snap_clone(self.snap, self.clone, self.server_list[0])

        # After cloning a volume wait for 5 second to start the volume
        sleep(5)

        # Starting clone volume
        redant.volume_start(self.clone, self.server_list[0])

        # Mounting a clone volume
        redant.execute_abstract_op_node(f"mkdir -p {self.mount1}",
                                        self.client_list[0])
        redant.volume_mount(self.server_list[0], self.clone, self.mount1,
                            self.client_list[0])

        # Validate clone volume mounted or not
        if not redant.is_mounted(self.clone, self.mount1, self.client_list[0],
                                 self.server_list[0]):
            raise Exception("Cloned Volume not mounted on mount point: "
                            f"{self.mount1}")

        # write files to mountpoint
        all_mounts_procs = []
        proc = redant.create_files('1k', self.mount1, self.client_list[0], 10)
        all_mounts_procs.append(proc)

        # Validate IO
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mount1
        }
        if not redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")

        self._check_arequal()

        # expanding volume
        ret = redant.expand_volume(self.server_list[0], self.clone,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to expand volume {self.clone}")

        # Start rebalance
        redant.rebalance_start(self.clone, self.server_list[0])

        # Wait for rebalance to complete
        if not redant.wait_for_rebalance_to_complete(self.clone,
                                                     self.server_list[0]):
            raise Exception("Rebalance is not yet complete "
                            f"on the volume {self.clone}")

        self._check_arequal()
