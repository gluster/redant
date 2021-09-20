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
    TC to check rebalance after add-brick when self-heal is in progress
"""

# disruptive;dist-rep,dist-arb
from random import choice
import traceback
from tests.d_parent_test import DParentTest


class TestAddBrickRebalanceWithSelfHeal(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_copy_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.list_of_io_processes, self.mounts)):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Start creating a few files on mount point.
        3. While file creation is going on, kill one of the bricks
           in the replica pair.
        4. After file creattion is complete collect arequal checksum
           on mount point.
        5. Bring back the brick online by starting volume with force.
        6. Check if all bricks are online and if heal is in progress.
        7. Add bricks to the volume and start rebalance.
        8. Wait for rebalance and heal to complete on volume.
        9. Collect arequal checksum on mount point and compare
           it with the one taken in step 4.
        """
        self.is_copy_running = False
        self.list_of_io_processes = []
        # Start I/O from mount point and wait for it to complete
        cmd = (f"cd {self.mountpoint}; for i in {{1..1000}} ; do "
               "dd if=/dev/urandom of=file$i bs=10M count=1; done")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        self.list_of_io_processes.append(proc)
        self.is_copy_running = True

        # Get a list of all the bricks to kill brick
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not brick_list:
            raise Exception("Empty brick list")

        # Kill brick process of a brick which is being removed
        brick = choice(brick_list)
        node, _ = brick.split(":")
        ret = redant.kill_process(node, process_names="glusterfsd")
        if not ret:
            raise Exception(f"Failed to kill brick process of brick {brick}")

        # Validate if I/O was successful or not.
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = redant.validate_io_procs(self.list_of_io_processes, self.mounts)
        if not ret:
            raise Exception("IO failed")
        self.is_copy_running = False

        # Collect arequal checksum before ops
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts)

        # Bring back the brick online by starting volume with force
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         brick_list)
        if not ret:
            raise Exception("Error in bringing back brick online")

        # Add brick to volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Trigger rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0],
                               force=True)

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=1200)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Wait for heal to complete
        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name):
            raise Exception("Heal is not yet completed")

        # Check for data loss by comparing arequal before and after ops
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts)
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum is NOT MATCHNG")
