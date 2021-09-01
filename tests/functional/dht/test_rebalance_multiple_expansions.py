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
    Add TC to test multiple volume expansions and rebalance
"""

from tests.d_parent_test import DParentTest

# disruptive;dist,dist-rep


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it
        2. Create some file on mountpoint
        3. Collect arequal checksum on mount point pre-rebalance
        4. Do the following 3 times:
        5. Expand the volume
        6. Start rebalance and wait for it to finish
        7. Collect arequal checksum on mount point post-rebalance
           and compare with value from step 3
        """

        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Create some file on mountpoint
        cmd = (f"cd {self.mountpoint}; "
               "for i in seq `1 500` ; do "
               "dd if=/dev/urandom of=file$i bs=10M count=1; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Collect arequal checksum before rebalance
        arequal_checksum_before = (redant.collect_mounts_arequal(
                                   self.mounts, self.mountpoint))

        for _ in range(3):
            # Add brick to volume
            if not (redant.expand_volume(self.server_list[0], self.vol_name,
                                         self.server_list, self.brick_roots)):
                raise Exception("Failed to expand volume")

            # Trigger rebalance and wait for it to complete
            redant.rebalance_start(self.vol_name, self.server_list[0],
                                   force=True)

            # Wait for rebalance to complete
            if not (redant.wait_for_rebalance_to_complete(self.vol_name,
                                                          self.server_list[0],
                                                          timeout=1200)):
                raise Exception("Rebalance operation has not yet completed.")

            # Collect arequal checksum after rebalance
            arequal_checksum_after = (redant.collect_mounts_arequal(
                                      self.mounts, self.mountpoint))

            # Check for data loss by comparing arequal before and after
            # rebalance
            if arequal_checksum_before != arequal_checksum_after:
                raise Exception("arequal checksum is NOT MATCHNG")
