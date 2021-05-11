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

Description:
    Create volume using bricks of deleted volume
"""
from tests.abstract_test import AbstractTest

# nonDisruptive;dist-rep


class TestCreateVolWithUsedBricks(AbstractTest):

    def run_test(self, redant):
        '''
        -> Create distributed-replica Volume
        -> Add 6 bricks to the volume
        -> Mount the volume
        -> Perform some I/O's on mount point
        -> unmount the volume
        -> Stop and delete the volume
        -> Create another volume using bricks of deleted volume
        -> Start the volume
        -> Execute IO command
        -> Mount the volume
        '''
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])
        redant.execute_io_cmd(f"rm -rf {self.mountpoint}",
                              self.client_list[0])
        redant.volume_stop(self.vol_name,
                           self.server_list[0], True)
        redant.volume_delete(self.vol_name, self.server_list[0])
        redant.volume_create(
            self.vol_name,
            self.server_list[0],
            self.vol_type_inf[self.conv_dict[self.volume_type]],
            self.server_list, self.brick_roots, True)
        redant.volume_start(self.vol_name, self.server_list[0])
        self.mountpoint = (f"/mnt/{self.vol_name}")
        redant.execute_io_cmd(f"mkdir -p {self.mountpoint}",
                              self.client_list[0])
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])
