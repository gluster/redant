"""
 Copyright (C) 2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module tests the snapshot Status when glusterd is
    restarted.
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
from tests.d_parent_test import DParentTest


class TestSnapshotGlusterdRestart(DParentTest):

    def run_test(self, redant):
        """
        Test Case:
        1. Create volume
        2. Create two snapshots with description
        3. Check snapshot status informations with snapname, volume name and
           without snap name/volname.
        4. Restart glusterd on all nodes
        5. Follow step3 again and validate snapshot
        """
        self.snapshots = [(f'snap-status-gd-restart-{i}') for i in range(2)]

        # Creating snapshot with description
        for snap in self.snapshots:
            redant.snap_create(self.vol_name, snap, self.server_list[0],
                               description='$p3C!@l C#@R@cT#R$')

        # Validate snapshot status information
        # Check snapshot status
        snap_stat = redant.get_snap_status(self.server_list[0])
        for snap in self.snapshots:
            if snap not in snap_stat:
                raise Exception("Failed to show snapshot status")

        # Check snapshot status using snap name
        snap_status = redant.get_snap_status_by_snapname(self.snapshots[0],
                                                         self.server_list[0])
        if self.snapshots[0] not in snap_status:
            raise Exception("Failed to show snapshot "
                            f"status for {self.snapshots[0]}")

        # Check snapshot status using volname
        snap_vol_sts = redant.get_snap_status_by_volname(self.vol_name,
                                                         self.server_list[0])
        for snap in self.snapshots:
            if snap not in snap_vol_sts:
                raise Exception("Failed to validate snapshot status")

        # Restart Glusterd on all node
        redant.restart_glusterd(self.server_list)

        # Check Glusterd status
        ret = redant.is_glusterd_running(self.server_list)
        if ret != 1:
            raise Exception("glusterd is not running")

        # Validate snapshot status information
        # Check snapshot status
        snap_stat = redant.get_snap_status(self.server_list[0])
        for snap in self.snapshots:
            if snap not in snap_stat:
                raise Exception("Failed to show snapshot status")

        # Check snapshot status using snap name
        snap_status = redant.get_snap_status_by_snapname(self.snapshots[0],
                                                         self.server_list[0])
        if self.snapshots[0] not in snap_status:
            raise Exception("Failed to show snapshot "
                            f"status for {self.snapshots[0]}")

        # Check snapshot status using volname
        snap_vol_sts = redant.get_snap_status_by_volname(self.vol_name,
                                                         self.server_list[0])
        for snap in self.snapshots:
            if snap not in snap_vol_sts:
                raise Exception("Failed to validate snapshot status")
