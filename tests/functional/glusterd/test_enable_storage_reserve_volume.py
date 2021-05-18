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
     This test case is authored to test posix storage.reserve option.
"""

# nonDisruptive;dist-rep
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        1) Create a distributed-replicated volume and start it.
        2) Enable storage.reserve option on the volume using below command,
        gluster volume set storage.reserve.
            let's say, set it to a value of 50.
        3) check df -h output of the mount point and backend bricks.
        """
        # Set volume option storage.reserve 50
        redant.set_volume_options(
            self.vol_name, {"storage.reserve ": 50},
            self.server_list[0])

        # Get the mount point
        mount_point = redant.es.get_mnt_pts_dict(self.vol_name)
        mount_point = mount_point[self.client_list[0]][0]

        # check df -h output
        cmd = f"df -h | grep -i {mount_point}"
        ret = redant.execute_command(cmd, self.client_list[0])
        out = ret['msg'][0].split(" ")[-2][:-1]

        if int(out) < 50:
            raise Exception("lesser than 50 percent in the list")
