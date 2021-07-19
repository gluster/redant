"""
  Copyright (C) 2021  Red Hat, Inc. <http://www.redhat.com>

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
snapshot creation and listing Invalid names
and parameters.
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. create volume and mount it
        2. create snapshot with invalid snap name
           should fail
        3. create snapshot
        4. snapshot list Invalid command should fail
        5. snapshot list Invalid parameters with multiple
           and non-existing volume name should fail
        """
        self.snap1 = "snap1"
        self.snapinvalid = "#64^@*)"
        self.volname1 = "vola1"
        # Creating snapshot with invalid snap name
        ret = redant.snap_create(self.vol_name, self.snapinvalid,
                                 self.server_list[0], excep=False)

        if ret['error_code'] == 0:
            raise Exception("Snap creation with snap name"
                            f" {self.snapinvalid} should have failed.")

        # Creating snapshot
        redant.snap_create(self.vol_name, self.snap1,
                           self.server_list[0])

        # validate snapshot list with volname
        ret = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(ret) > 1:
            raise Exception("More than 1 snapshot present even though only"
                            " 1 was created.")

        # listing snapshot with invalid volume name which should fail
        ret = redant.get_snap_list(self.server_list[0], self.volname1,
                                   excep=False)
        if ret['msg']['opRet'] != '-1':
            raise Exception(f"Snap listing with volname {self.volname1}"
                            " should've failed.")

        # snapshot list with multiple and non-existing volume
        cmd = (f"gluster snap list {self.vol_name} {self.volname1} --xml"
               " --mode=script")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception(f"The command {cmd} should've failed as invalid"
                            " command.")
