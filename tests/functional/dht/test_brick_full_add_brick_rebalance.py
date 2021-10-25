"""
 Copyright (C) 2020-2021 Red Hat, Inc. <http://www.redhat.com>

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
    TC to check add-brick when the existing bricks are full, and do
    rebalance
"""

# disruptive;dist-rep,dist-arb
import string
from random import choice
from tests.d_parent_test import DParentTest


class TestBrickFullAddBrickRebalance(DParentTest):

    @staticmethod
    def _get_random_string():
        letters = string.ascii_lowercase
        return ''.join(choice(letters) for _ in range(5))

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create a data set on the client node such that all the available
           space is used and "No space left on device" error is generated.
        3. Set cluster.min-free-disk to 30%.
        4. Add bricks to the volume, trigger rebalance and wait for rebalance
           to complete.
        """
        # Create a data set on the client node such that all the available
        # space is used and "No space left on device" error is generated
        bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])

        # Calculate the usable size and fill till it reaches
        # min free limit
        usable_size = redant.get_usable_size_per_disk(bricks[0])
        if not usable_size:
            raise Exception("Failed to get the usable size of the brick")

        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the volume subvols")

        filename = "abc"
        for subvol in subvols:
            while (subvols[redant.find_hashed_subvol(subvols, "",
                                                     filename)[1]]
                   == subvol):
                filename = self._get_random_string()

            cmd = f"fallocate -l {usable_size}G {self.mountpoint}/{filename}"
            ret = redant.execute_abstract_op_node(cmd, self.client_list[0],
                                                  False)
            ret_val = ret['error_code']
            err_msg = 'No space left on device'
            if ret['error_code'] and ret['error_msg'] == err_msg:
                ret_val = 0

            if ret_val != 0:
                raise Exception("Failed to fill disk to min free limit")

        # Try to perfrom I/O from mount point(This should fail)
        ret = redant.execute_abstract_op_node("fallocate -l 50G "
                                              f"{self.mountpoint}/mfile",
                                              self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Able to do I/O even when disks are "
                            "filled to min free limit")

        # Set cluster.min-free-disk to 30%
        options = {'cluster.min-free-disk': '30%'}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Add brick to volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Trigger rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0], force=True)

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=1200)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")
