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
    TC to check rebalance of volume after filling up one disk/brick

 *Flaky Test*
 Reason: All linkto files are not removed after rebalance
"""

# disruptive;dist
from random import choice
from copy import deepcopy
import string
from tests.d_parent_test import DParentTest


class TestOneBrickFullAddBrickRebalance(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 3

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    @staticmethod
    def _get_random_string():
        letters = string.ascii_lowercase
        return ''.join(choice(letters) for _ in range(10))

    def run_test(self, redant):
        """
        Test case:
        1. Create a pure distribute volume with 3 bricks.
        2. Start it and mount it on client.
        3. Fill one disk of the volume till it's full
        4. Add brick to volume, start rebalance and wait for it to complete.
        5. Check arequal checksum before and after add brick should be same.
        6. Check if link files are present on bricks or not.
        """
        # Fill few bricks till it is full
        bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not bricks:
            raise Exception("Failed ot get the bricks list")

        # Calculate the usable size and fill till it reaches
        # min free limit
        usable_size = redant.get_usable_size_per_disk(bricks[0])
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        fname = "abc"

        # Create directories in hierarchy
        dirp = "dir1/dir2/"
        path = f"{self.mountpoint}/{dirp}"
        redant.create_dir(self.mountpoint, "dir1/dir2", self.client_list[0])

        for _ in range(0, usable_size):
            # Create files inside directories
            while (subvols[redant.find_hashed_subvol(subvols, dirp,
                                                     fname)[1]][0]
                   != subvols[0][0]):
                fname = self._get_random_string()
            cmd = f"fallocate -l 1G {path}{fname}"
            redant.execute_abstract_op_node(cmd, self.client_list[0])
            fname = self._get_random_string()

        # Collect arequal checksum before ops
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts)

        # Add brick to volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.volname}")

        # Trigger rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0],
                               force=True)

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=1800)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Check for data loss by comparing arequal before and after ops
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts)
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum is NOT MATCHNG")

        # Check if linkto files exist or not as rebalance is already
        # completed we shouldn't be seeing any linkto files
        for brick in bricks:
            node, path = brick.split(":")
            path = f"{path}/{dirp}"
            list_of_files = redant.get_dir_contents(path, node)
            if list_of_files is None:
                raise Exception("Unable to get files")

            for filename in list_of_files:
                ret = redant.get_dht_linkto_xattr(node, f"{path}{filename}",
                                                  excep=False)
                if ret['error_code'] == 0:
                    raise Exception("Unexpected: file is linkto")
