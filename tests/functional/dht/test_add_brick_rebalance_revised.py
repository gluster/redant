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
    TC to check rebalance after add-brick with hardlinks and sticky-bit
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
from tests.d_parent_test import DParentTest


class TestAddBrickRebalanceRevised(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _run_command_50_times(self, operation):
        """
        Run a command 50 times on the mount point and display msg if fails
        """
        cmd = (f"cd {self.mountpoint}; for i in {{1..50}}; "
               f"do {operation};done")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _add_bricks_to_volume(self):
        """Add bricks to the volume"""
        ret = self.redant.expand_volume(self.server_list[0], self.vol_name,
                                        self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

    def _trigger_rebalance_and_wait(self, rebal_force=False):
        """Start rebalance with or without force and wait"""
        # Trigger rebalance on volume
        self.redant.rebalance_start(self.vol_name, self.server_list[0],
                                    force=rebal_force)

        # Wait for rebalance to complete
        ret = self.redant.wait_for_rebalance_to_complete(self.vol_name,
                                                         self.server_list[0],
                                                         timeout=1200)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

    def _check_if_files_are_skipped_or_not(self):
        """Check if files are skipped or not"""
        rebal_status = self.redant.get_rebalance_status(self.vol_name,
                                                        self.server_list[0])
        ret = int(rebal_status['aggregate']['skipped'])
        if ret == 0:
            raise Exception("Hardlink rebalance skipped")

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it using fuse.
        2. Create 50 files on the mount point and create 50 hardlinks for the
           files.
        3. After the files and hard links creation is complete, add bricks to
           the volume and trigger rebalance on the volume.
        4. Wait for rebalance to complete and check if files are skipped
           or not.
        5. Trigger rebalance on the volume with force and repeat step 4.
        """
        # Tuple of ops to be done
        ops = ("dd if=/dev/urandom of=file_$i bs=1M count=1",
               "ln file_$i hardfile_$i",)

        # Create 50 files on the mount point and create 50 hard links
        # for the files.
        for operation in ops:
            self._run_command_50_times(operation)

        # Collect arequal checksum before add brick op
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts)

        # After the file creation is complete, add bricks to the volume
        self._add_bricks_to_volume()

        # Trigger rebalance on the volume, wait for it to complete
        self._trigger_rebalance_and_wait()

        # Check if hardlinks are skipped or not
        self._check_if_files_are_skipped_or_not()

        # Trigger rebalance with force on the volume, wait for it to complete
        self._trigger_rebalance_and_wait(rebal_force=True)

        # Check if hardlinks are skipped or not
        self._check_if_files_are_skipped_or_not()

        # Compare arequals checksum before and after rebalance
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts)
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum is NOT MATCHNG")

        # Cleanup volumes for next TC
        redant.cleanup_volumes(self.server_list, self.vol_name)

        # Setup the volume again
        conf_hash = self.vol_type_inf[self.volume_type]
        redant.setup_volume(self.vol_name, self.server_list[0],
                            conf_hash, self.server_list,
                            self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                        self.client_list[0])
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        # Test case 2: test_add_brick_rebalance_with_sticky_bit:
        """
        Steps:
        1. Create a volume, start it and mount it using fuse.
        2. Create 50 files on the mount point and set sticky bit to the files.
        3. After the files creation and sticky bit addition is complete,
           add bricks to the volume and trigger rebalance on the volume.
        4. Wait for rebalance to complete.
        5. Check for data corruption by comparing arequal before and after.
        """
        # Tuple of ops to be done
        ops = ("dd if=/dev/urandom of=file_$i bs=1M count=1",
               "chmod +t file_$i")

        # Create 50 files on the mount point and enable sticky bit.
        for operation in ops:
            self._run_command_50_times(operation)

        # Collect arequal checksum before add brick op
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts)

        # After the file creation and sticky bit addtion is complete,
        # add bricks to the volume
        self._add_bricks_to_volume()

        # Trigger rebalance on the volume, wait for it to complete
        self._trigger_rebalance_and_wait()

        # Compare arequals checksum before and after rebalance
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts)
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum is NOT MATCHNG")
