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
    TC to check replace-brick after add-brick and then rebalance with
    fix_layout
"""

# disruptive;dist-rep,dist-arb
from random import choice
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestAddBrickReplaceBrickFixLayout(DParentTest):

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
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _replace_a_old_added_brick(self, brick_to_be_replaced, new_brick):
        """Replace a old brick from the volume"""
        ret = (self.redant.replace_brick_from_volume(self.vol_name,
               self.server_list[0], self.server_list,
               src_brick=brick_to_be_replaced, dst_brick=new_brick))
        if not ret:
            raise Exception(f"Failed to replace brick {brick_to_be_replaced}")

    def _check_trusted_glusterfs_dht_on_all_bricks(self):
        """Check trusted.glusterfs.dht xattr on the backend bricks"""
        bricks = self.redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if not bricks:
            raise Exception("Failed to get the brick list")

        fattr_value = []
        for brick_path in bricks:
            node, path = brick_path.split(":")
            ret = self.redant.get_fattr(path, "trusted.glusterfs.dht", node)
            fattr_value += [ret[1].split('=')[1].rstrip("\n")]
        if len(set(fattr_value)) == 4:
            raise Exception("Value of trusted.glusterfs.dht is not as "
                            "expected")

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create files and dirs on the mount point.
        3. Add bricks to the volume.
        4. Replace 2 old bricks to the volume.
        5. Trigger rebalance fix layout and wait for it to complete.
        6. Check layout on all the bricks through trusted.glusterfs.dht.
        """
        # Create directories with some files on mount point
        cmd = (f"cd {self.mountpoint}; for i in {{1..10}}; do mkdir dir$i;"
               " for j in {1..5}; do dd if=/dev/urandom of=dir$i/file$j bs=1M"
               " count=1; done; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Orginal brick list before add brick
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not brick_list:
            raise Exception("Empty brick list")

        # Add bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception("Failed to expand volume")

        # Replace 2 old bricks to the volume
        for i in range(0, 2):
            brick = choice(brick_list)
            sbrick_host, sbrick_root = brick.split(':')
            dbrick_root = sbrick_root[0:brick.split(':')[1].rfind("/")]
            dbrick = f"{sbrick_host}:{dbrick_root}/new_replaced_brick-{i}"
            self._replace_a_old_added_brick(brick, dbrick)
            brick_list.remove(brick)

        # Start rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0],
                               fix_layout=True)

        ret = redant.wait_for_fix_layout_to_complete(self.server_list[0],
                                                     self.vol_name,
                                                     timeout=800)
        if not ret:
            raise Exception("Rebalance failed on volume")

        # Check layout on all the bricks through trusted.glusterfs.dht
        self._check_trusted_glusterfs_dht_on_all_bricks()
