"""
 Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
    TC verifies brick layout after add-brick followed by remove brick
"""

# disruptive;rep
import traceback
from tests.d_parent_test import DParentTest


class TestAddBrickFollowedByRemoveBrick(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete if the TC fails early
        """
        try:
            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mounts)):
                    raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _add_brick_and_rebalance_and_check_layout(self):
        """Add brick and wait for rebalance to complete"""

        # Add brick to volume
        ret = self.redant.expand_volume(self.server_list[0], self.vol_name,
                                        self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Trigger rebalance and wait for it to complete
        self.redant.rebalance_start(self.vol_name, self.server_list[0],
                                    force=True)

        # Wait for rebalance to complete
        ret = self.redant.wait_for_rebalance_to_complete(self.vol_name,
                                                         self.server_list[0],
                                                         timeout=1200)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Check the layout of bricks
        ret = self.redant.is_layout_complete(self.server_list[0],
                                             self.vol_name, "/")
        if not ret:
            raise Exception(f"Volume {self.vol_name}: Layout is not complete")

    def _remove_brick_from_volume(self):
        """Remove bricks from volume"""
        ret = self.redant.shrink_volume(self.server_list[0], self.vol_name,
                                        rebal_timeout=2000)
        if not ret:
            raise Exception("Failed to remove-brick from volume")

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it to a client.
        2. Start I/O on volume.
        3. Add brick and trigger rebalance, wait for rebalance to complete.
           (The volume which was 1x3 should now be 2x3)
        4. Add brick and trigger rebalance, wait for rebalance to complete.
           (The volume which was 2x3 should now be 3x3)
        5. Remove brick from volume such that it becomes a 2x3.
        6. Remove brick from volume such that it becomes a 1x3.
        7. Wait for I/O to complete and check for any input/output errors in
           both client and rebalance logs.
        """
        # Start I/O on mount point
        self.is_io_running = False
        self.all_mounts_procs = []
        proc = redant.create_deep_dirs_with_files(self.mountpoint, 10, 5, 5,
                                                  5, 5, self.client_list[0])
        self.all_mounts_procs.append(proc)
        self.is_io_running = True

        # Convert 1x3 to 2x3 and then convert 2x3 to 3x3
        for _ in range(0, 2):
            self._add_brick_and_rebalance_and_check_layout()

        # Convert 3x3 to 2x3 and then convert 2x3 to 1x3
        for _ in range(0, 2):
            self._remove_brick_from_volume()

        # Validate I/O processes running on the nodes
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")
        self.is_io_running = False

        # Check for Input/output errors in rebalance logs
        particiapting_nodes = []
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not brick_list:
            raise Exception("Failed to get the brick list")

        for brick in brick_list:
            node, _ = brick.split(':')
            particiapting_nodes.append(node)

        rebal_file = f"/var/log/glusterfs/{self.vol_name}-rebalance.log"
        for server in particiapting_nodes:
            ret = redant.occurences_of_pattern_in_file(server,
                                                       "Input/output error",
                                                       rebal_file)
            if ret != 0 or ret == -1:
                raise Exception("[Input/output error] present in rebalance "
                                "log file or failed to find pattern in file")

        # Check for Input/output errors in client logs
        mnt_file = f"/var/log/glusterfs/mnt-{self.vol_name}.log"
        ret = redant.occurences_of_pattern_in_file(self.client_list[0],
                                                   "Input/output error",
                                                   mnt_file)
        if ret != 0 or ret == -1:
            raise Exception("[Input/output error] present in client log "
                            "file or failed to find pattern in file")
