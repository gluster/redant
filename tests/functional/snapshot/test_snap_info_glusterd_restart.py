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
    TC to test the snapshot information after glusterd is restarted.
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
from tests.d_parent_test import DParentTest


class TestSnapshotInfoGlusterdRestart(DParentTest):

    def _snapshot_info(self):
        """
        This section checks the snapshot information:
        * Using snapname
        * Using volname
        * Without using snapname or volname
        """
        # Check snapshot info using snapname
        for snap in self.snapshots:
            ret = self.redant.get_snap_info_by_snapname(snap,
                                                        self.server_list[0])
            if not ret:
                raise Exception("Failed to get snap info")
            if ret['name'] != snap:
                raise Exception(f"Failed to show snapshot info for {snap}")

        # Check snapshot info using volname
        ret = self.redant.get_snap_info_by_volname(self.vol_name,
                                                   self.server_list[0])
        if not ret:
            raise Exception("Failed to get snap info")
        if ret['originVolume']['name'] != self.vol_name:
            raise Exception("Failed to show snapshot info for "
                            f"{self.vol_name}")

        # Validate snapshot information without using snapname or volname
        ret = self.redant.get_snap_info(self.server_list[0])
        if not ret:
            raise Exception("Failed to get snap info")

        for i, snap in enumerate(self.snapshots):
            if ret[i]['name'] != snap:
                raise Exception("Failed to validate snap information")

    def run_test(self, redant):
        """
        * Create multiple snapshots
        * Check snapshot info
          - Without using snapname or volname
          - Using snapname
          - Using volname
        * Restart glusterd on all servers
        * Repeat the snapshot info step for all the three scenarios
          mentioned above
        """
        self.snapshots = [(f"snap-test-snap-info-gd-restart-{i}")
                          for i in range(0, 2)]

        # Create snapshots with description
        for snap in self.snapshots:
            redant.snap_create(self.vol_name, f"{snap}",
                               self.server_list[0],
                               description="$p3C!@l C#@R@cT#R$")

        # Perform the snapshot info tests before glusterd restart
        self._snapshot_info()

        # Restart Glusterd on all servers
        redant.restart_glusterd(self.server_list)

        # Wait for glusterd to be online and validate glusterd running on all
        # server nodes
        if not redant.wait_for_glusterd_to_start(self.server_list):
            raise Exception(f"Glusterd is not running on {self.server_list}")

        # Check if peers are connected
        if not redant.wait_for_peers_to_connect(self.server_list,
                                                self.server_list[0]):
            raise Exception("Peers are not yet in connected state")

        # perform the snapshot info tests after glusterd restart
        self._snapshot_info()
