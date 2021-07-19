"""
  Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
snapshot deletion with snapname, with volumename
and delete all snapshot commands.

"""

# disruptive;rep,disp,dist,dist-rep,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. create a volume and mount it
        2. create 9 snapshots of volume
        3. delete snapshot with snapname
        4. delete other snapshots with volume name
        5. create one more snapshot
        6. delete created snapshot with snap delete command
        """

        # Creating snapshot
        for snap_count in range(0, 9):
            self.snap_name = f"{self.vol_name}-snap{snap_count}"
            redant.snap_create(self.vol_name, self.snap_name,
                               self.server_list[0])

        # deleting snapshot with snap name
        for snap_count in range(0, 3):
            self.snap_name = f"{self.vol_name}-snap{snap_count}"
            redant.snap_delete(self.snap_name, self.server_list[0])

        # delete all snapshot of volume
        redant.snap_delete_by_volumename(self.vol_name, self.server_list[0])

        # create a new snapshot
        self.snap_name = f"{self.vol_name}-snapy1"
        redant.snap_create(self.vol_name, self.snap_name,
                           self.server_list[0])

        # Delete the snapshot.
        redant.snap_delete(self.snap_name, self.server_list[0])
