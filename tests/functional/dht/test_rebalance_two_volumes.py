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
"""
# disruptive;dist,dist-rep

import traceback
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestRebalanceTwoVolumes(DParentTest):

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it
        2. Create a 2nd volume, start it and mount it
        3. Create files on mount points
        4. Collect arequal checksum on mount point pre-rebalance
        5. Expand the volumes
        6. Start rebalance simultaneously on the 2 volumes
        7. Wait for rebalance to complete
        8. Collect arequal checksum on mount point post-rebalance
           and compare with value from step 4
        """
        # Create a 2nd volume, start and mount it
        self.second_vol_name = "second_volume"
        self.second_mountpoint = f"/mnt/{self.second_vol_name}"
        conf_dict = deepcopy(self.vol_type_inf[self.volume_type])
        if self.volume_type == "dist":
            factor = 3
        elif self.volume_type == "dist-rep":
            factor = 6
        brick_dict, brick_cmd = redant.form_brick_cmd(self.server_list,
                                                      self.brick_roots,
                                                      self.second_vol_name,
                                                      factor)
        redant.volume_create_with_custom_bricks(self.second_vol_name,
                                                self.server_list[0],
                                                conf_dict, brick_cmd,
                                                brick_dict, force=True)
        redant.volume_start(self.second_vol_name, self.server_list[0])
        self.redant.execute_abstract_op_node("mkdir -p "
                                             f"{self.second_mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.second_vol_name,
                                 self.second_mountpoint, self.client_list[0])

        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Start I/O from mount point for volume 1 and wait for it to complete
        cmd = (f"cd {self.mountpoint}; for i in {{1..1000}} ; do "
               "dd if=/dev/urandom of=file$i bs=10M count=1; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Start I/O from mount point for volume 2 and wait for it to complete
        cmd = (f"cd {self.second_mountpoint}; for i in {{1..1000}} ; do "
               "dd if=/dev/urandom of=file$i bs=10M count=1; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Collect arequal checksum before rebalance
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts[0])

        # Add bricks to volumes
        for volume in (self.vol_name, self.second_vol_name):
            ret = redant.expand_volume(self.server_list[0],
                                       volume, self.server_list,
                                       self.brick_roots, force=True)
            if not ret:
                raise Exception("Failed to expand volume")

        # Trigger rebalance
        for volume in (self.vol_name, self.second_vol_name):
            redant.rebalance_start(volume, self.server_list[0],
                                   force=True)

        # Wait for rebalance to complete
        for volume in (self.vol_name, self.second_vol_name):
            ret = redant.wait_for_rebalance_to_complete(volume,
                                                        self.server_list[0],
                                                        timeout=1200)
            if not ret:
                raise Exception("Rebalance is not yet complete on the volume "
                                f"{volume}")

        # Collect arequal checksum after rebalance
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts[0])

        # Check for data loss by comparing arequal before and after rebalance
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum in NOT equal")
