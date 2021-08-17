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
snapshot information commands.

"""

from tests.d_parent_test import DParentTest

# disruptive;rep,dist,disp,dist-rep,dist-disp


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Create volumes
        2. create multiple snapshots
        3. Check snapshot info for snapshots created
           using snap name, using volume name and
           without using snap name and volume name
        """
        snap_list = []
        # Creating snapshot with description
        for count in range(0, 2):
            snap_name = f"{self.vol_name}-snap{count}"
            redant.snap_create(self.vol_name, snap_name, self.server_list[0],
                               description='$p3C!@l C#@R@cT#R$')
            snap_list.append(snap_name)

        # Check snapshot info using snap name
        snap_info_chk = redant.get_snap_info_by_snapname(snap_list[1],
                                                         self.server_list[0])
        if not snap_info_chk:
            raise Exception("Snap info obtained using snapname is None")

        # Check snapshot info using volname
        snap_vol_info = redant.get_snap_info_by_volname(self.vol_name,
                                                        self.server_list[0])
        if not snap_vol_info:
            raise Exception("Snap info obtained using volname is None")

        # Validate snapshot information
        info_snaps = redant.get_snap_info(self.server_list[0])
        if not info_snaps:
            raise Exception("Snap info obtained is None")
        snap_keys = info_snaps.keys()
        for snap in snap_list:
            if snap not in info_snaps.keys():
                raise Exception(f"{snap} not present in {info_snaps.keys()}")
