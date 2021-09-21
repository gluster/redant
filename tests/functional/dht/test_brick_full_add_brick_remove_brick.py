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
    TC to check brick full, then add-brick and remove-brick
"""

# disruptive;dist-rep,dist-arb
from random import choice
import string
from tests.d_parent_test import DParentTest


class TestBrickFullAddBrickRemoveBrickRebalance(DParentTest):

    @staticmethod
    def _get_random_string():
        letters = string.ascii_lowercase
        return ''.join(choice(letters) for _ in range(5))

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Fill few bricks till min-free-limit is reached.
        3. Add brick to the volume.(This should pass.)
        4. Set cluster.min-free-disk to 30%.
        5. Remove bricks from the volume.(This should pass.)
        6. Check for data loss by comparing arequal before and after.
        """
        # Fill few bricks till it is full
        bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])

        # Calculate the usable size and fill till it reaches
        # min free limit
        usable_size = redant.get_usable_size_per_disk(bricks[0])
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        filename = "abc"
        for _ in range(0, usable_size):
            while (subvols[redant.find_hashed_subvol(subvols, "",
                                                     filename)[1]]
                   == subvols[0]):
                filename = self._get_random_string()

            cmd = f"fallocate -l 1G {self.mountpoint}/{filename}"
            ret = redant.execute_abstract_op_node(cmd, self.client_list[0],
                                                  False)
            ret_val = ret['error_code']
            err_msg = 'No space left on device'
            if ret['error_code'] and ret['error_msg'] == err_msg:
                ret_val = 0

            if ret_val != 0:
                raise Exception("Failed to fill disk to min free limit")

            filename = self._get_random_string()

        # Collect arequal checksum before ops
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts)

        # Add brick to volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Set cluster.min-free-disk to 30%
        options = {'cluster.min-free-disk': '30%'}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Remove bricks from the volume
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   rebal_timeout=1800)
        if not ret:
            raise Exception("Failed to remove-brick from volume")

        # Check for data loss by comparing arequal before and after ops
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts)
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum is NOT MATCHNG")
