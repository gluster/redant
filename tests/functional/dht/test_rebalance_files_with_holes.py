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

 You should have received a copy of the GNU General Public License along`
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    TC to check rebalance on files with holes
"""

# disruptive;dist,rep,disp,arb,dist-rep,dist-disp,dist-arb
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestAddBrickRebalanceFilesWithHoles(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.vol_name = f"testvol_{self.volume_type}"
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def run_test(self, redant):
        """
        Case 1: test_add_brick_rebalance_files_with_holes
        Test case:
        1. Create a volume, start it and mount it using fuse.
        2. On the volume root, create files with holes.
        3. After the file creation is complete, add bricks to the volume.
        4. Trigger rebalance on the volume.
        5. Wait for rebalance to complete.
        """
        # On the volume root, create files with holes
        cmd = (f"cd {self.mountpoint};for i in {{1..5000}}; do dd "
               "if=/dev/urandom of=file_with_holes$i bs=1M count=1"
               " seek=100M; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # After the file creation is complete, add bricks to the volume
        force = False
        if self.volume_type == "disp" or self.volume_type == "dist-disp":
            force = True
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=force)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Trigger rebalance on the volume
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=9000)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Cleanup volume
        redant.cleanup_volumes(self.server_list, self.vol_name)

        # Case 2: TestRemoveBrickRebalanceFilesWithHoles
        volume_types = ["dist-rep", "dist-arb", "dist-disp", "dist"]
        if self.volume_type in volume_types:
            """
            Test case:
            1. Create a volume, start it and mount it using fuse.
            2. On the volume root, create files with holes.
            3. After the file creation is complete, remove-brick from volume.
            4. Wait for remove-brick to complete.
            """
            redant.setup_volume(self.vol_name, self.server_list[0],
                                self.vol_type_inf[self.volume_type],
                                self.server_list, self.brick_roots)
            self.mountpoint = (f"/mnt/{self.vol_name}")
            redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                            self.client_list[0])
            redant.volume_mount(self.server_list[0], self.vol_name,
                                self.mountpoint, self.client_list[0])

            # On the volume root, create files with holes
            cmd = (f"cd {self.mountpoint}; for i in {{1..2000}}; do dd"
                   " if=/dev/urandom of=file_with_holes$i bs=1M count=1"
                   " seek=100M; done")
            redant.execute_abstract_op_node(cmd, self.client_list[0])

            # After the file creation is complete, remove-brick from volume
            # Wait for remove-brick to complete
            ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                       rebal_timeout=16000)
            if not ret:
                raise Exception("Failed to remove-brick from volume")
