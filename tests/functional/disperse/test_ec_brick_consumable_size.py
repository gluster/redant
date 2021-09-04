"""
  Copyright (C) 2018-2020 Red Hat, Inc. <http://www.redhat.com>

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

EcBrickConsumableSize:
    This test verifies that the size of the volume will be
    'number of data bricks * least of brick size'.
"""

# disruptive;disp,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    def _get_min_brick(self):
        # Returns the brick with min size
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        min_brick_size = -1
        min_brick = None
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            brick_size = self.redant.get_size_of_mountpoint(brick_path,
                                                            brick_node)
            if ((brick_size) and (min_brick_size == -1)
                    or (int(min_brick_size) > int(brick_size))):
                min_brick_size = brick_size
                min_brick = brick
        return min_brick, min_brick_size

    def _get_consumable_vol_size(self, min_brick_size):
        # Calculates the consumable size of the volume created
        vol_info = self.redant.get_volume_info(self.server_list[0],
                                               self.vol_name)
        if not vol_info:
            raise Exception('Not able to get volume info')

        disp_data_bricks = (int(vol_info[self.vol_name]['disperseCount'])
                            - int(vol_info[self.vol_name]['redundancyCount']))
        dist_count = int(vol_info[self.vol_name]['distCount'])
        consumable_size = ((int(min_brick_size) * int(disp_data_bricks))
                           * int(dist_count))
        return consumable_size, dist_count

    def run_test(self, redant):
        """
        1. Obtain the volume size
        2. Retrieve the minimum brick size
        3. Calculate the consumable size
        4. Verify the volume size
        5. Write to the available size and try to write more
        6. Cleanup the mounts to verify
        7. Vol size after bringing down the brick with smallest size should
           not be greater than the actual size
        """
        # Obtain the volume size
        client = self.client_list[0]
        mpoint = self.mountpoint
        vol_size = redant.get_size_of_mountpoint(mpoint, client)
        if not vol_size:
            raise Exception(f"Unable to get the volsize of {self.volname}")

        # Retrieve the minimum brick size
        min_brick, min_brick_size = self._get_min_brick()

        # Calculate the consumable size
        consumable_size, dist_count = (
            self._get_consumable_vol_size(min_brick_size))

        # Verify the volume size is in allowable range
        # Volume size should be above 98% of consumable size.
        delta = (100 - ((float(vol_size)/float(consumable_size)) * 100))
        if delta >= 2:
            raise Exception("Volume size is not in allowable range")

        # Write to the available size
        block_size = 1024
        write_size = ((int(vol_size) * 0.95 * int(block_size))
                      / (int(dist_count)))
        for i in range(0, dist_count):
            cmd = f'fallocate -l {write_size} {mpoint}/testfile{i}'
            redant.execute_abstract_op_node(cmd, client)

        # Try writing more than the available size
        write_size = ((int(vol_size) * int(block_size)) * 1.2)
        cmd = f'fallocate -l {write_size} {mpoint}/testfile2'
        ret = redant.execute_abstract_op_node(cmd, client, False)
        if ret['error_code'] != 0:
            raise Exception("Writing file of more than available "
                            "size passed on volume %s")

        # Cleanup the mounts to verify
        cmd = (f'rm -rf -v {self.mountpoint}/*')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bring down the smallest brick
        redant.bring_bricks_offline(self.vol_name, min_brick)
        if not redant.are_bricks_offline(self.vol_name, min_brick,
                                         self.server_list[0]):
            raise Exception(f"Bricks {min_brick} are not offline")

        # Find the volume size post brick down
        post_vol_size = redant.get_size_of_mountpoint(mpoint, client)
        if not post_vol_size:
            raise Exception(f"Unable to get the volsize of {self.volname}")

        # Vol size after bringing down the brick with smallest size should
        # not be greater than the actual size
        if post_vol_size >= vol_size:
            raise Exception("The volume size after bringing down the volume "
                            "is greater than the initial")
