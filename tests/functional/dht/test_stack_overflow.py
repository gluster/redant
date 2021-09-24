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

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Description: Tests to check that there is no stack overflow
             in readdirp with parallel-readdir enabled.
"""

# disruptive;dist,rep,disp,dist-rep,dist-disp,arb,dist-arb

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Steps :
        1) Create a volume.
        2) Mount the volume using FUSE.
        3) Enable performance.parallel-readdir and
           performance.readdir-ahead on the volume.
        4) Create 10000 files on the mount point.
        5) Add-brick to the volume.
        6) Perform fix-layout on the volume (not rebalance).
        7) From client node, rename all the files, this will result in creation
           of linkto files on the newly added brick.
        8) Do ls -l (lookup) on the mount-point.
        """
        # Enable performance.parallel-readdir and
        # performance.readdir-ahead on the volume
        options = {"performance.parallel-readdir": "enable",
                   "performance.readdir-ahead": "enable"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0], True)

        # Creating 10000 files on volume root
        cmd = f'touch {self.mountpoint}/file{{1..10000}}_0'
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Add bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Perform fix-layout on the volume
        redant.rebalance_start(self.vol_name, self.server_list[0],
                               fix_layout=True)

        # Wait for fix-layout to complete
        ret = redant.wait_for_fix_layout_to_complete(self.server_list[0],
                                                     self.vol_name,
                                                     timeout=3000)
        if not ret:
            raise Exception("Rebalance failed on volume")

        # Rename all files from client node
        for i in range(1, 10000):
            ret = redant.move_file(self.client_list[0],
                                   f'{self.mountpoint}/file{i}_0',
                                   f'{self.mountpoint}/file{i}_1')

        # Perform lookup from the mount-point
        cmd = f"ls -lR {self.mountpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Reset the volume options set
        vol_options = ['performance.parallel-readdir',
                       'performance.readdir-ahead']
        for opt in vol_options:
            redant.reset_volume_option(self.vol_name, opt,
                                       self.server_list[0])
