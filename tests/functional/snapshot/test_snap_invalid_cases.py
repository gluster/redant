"""
  Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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

Test Cases in this module tests the
snapshot Status and Info for Invalid cases.

"""

# disruptive;rep,dist,disp,dist-rep,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Create volumes
        2. create multiple snapshots
        3. Show status of non existing snapshots
        4. Show info of non existing snapshots
        5. Show status of snaps of non-existing volumes
        6. Show info of snaps of non-existing volume
        7. status of snapshots with invalid command
        8. Info of snapshots with invalid command
        """

        self.snap5 = "snap5"
        self.snap1 = "snap1"
        self.volname1 = "volume1"

        # Creating snapshot:
        for count in range(1, 3):
            self.snap_name = f"snap{count}"
            redant.snap_create(self.vol_name, self.snap_name,
                               self.server_list[0])

        # Check snapshot info for non-existing snapshot
        ret = redant.get_snap_info_by_snapname(self.snap5,
                                               self.server_list[0],
                                               excep=False)
        if ret is not None:
            raise Exception(f"Snap info for {self.snap5}, a non existant snap"
                            " didn't fail.")

        # Check snapshot status for non-existing snapshot
        ret = redant.get_snap_status_by_snapname(self.snap5,
                                                 self.server_list[0])
        if ret is not None:
            raise Exception(f"Snap status for {self.snap5}, a non existant "
                            "snap didn't fail")

        # Check snapshot info for non-existing volume
        ret = redant.get_snap_info_by_volname(self.volname1,
                                              self.server_list[0], excep=False)
        if ret is not None:
            raise Exception(f"Snap info for {self.volname1}, a non existant"
                            " volume didn't fail.")

        # Invalid command
        cmd = "gluster snapshot snap1 status"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception(f"The command {cmd} should've failed.")

        # Invalid command
        cmd = "gluster snapshot snap1 info"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception(f"The command {cmd} should've failed.")
