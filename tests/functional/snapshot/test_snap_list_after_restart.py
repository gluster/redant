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
    Verify snap list before and after glusterd restart.
"""

from tests.d_parent_test import DParentTest

# disruptive;rep,dist,disp,dist-rep,dist-disp


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Verify snapshot list before and after glusterd restart

        * Create 3 snapshots of the volume
        * Delete one snapshot
        * List all snapshots created
        * Restart glusterd on all nodes
        * List all snapshots
          All snapshots must be listed except the one that was deleted
        """

        snap_names = []
        # Create snapshots
        for count in range(3):
            snap_name = f"{self.vol_name}-snap{count}"
            snap_names.append(snap_name)
            redant.snap_create(self.vol_name, snap_name, self.server_list[0])

        # List the snapshots and validate with snapname
        snap_list = redant.get_snap_list(self.server_list[0])
        if len(snap_list) != 3:
            raise Exception(f"Expected 3 snaps but got {snap_list}")
        for snap in snap_names:
            if snap not in snap_list:
                raise Exception(f"{snap} not in {snap_list}")

        # Delete one snapshot
        redant.snap_delete(snap_names[0], self.server_list[0])

        # List the snapshots and validate with snapname
        snap_list = redant.get_snap_list(self.server_list[0])
        if len(snap_list) != 2:
            raise Exception(f"Expected 2 snaps but got {snap_list}")
        for snap in snap_names[1:]:
            if snap not in snap_list:
                raise Exception(f"{snap} not in {snap_list}")

        # Restart glusterd on all the servers
        redant.restart_glusterd(self.server_list)

        # Wait for glusterd to be online
        if not redant.wait_for_glusterd_to_start(self.server_list):
            raise Exception("Glusterd is not running in some of the"
                            " servers")

        # Wait for peers to get connected.
        if not redant.wait_till_all_peers_connected(self.server_list):
            raise Exception("Peer handshake not complete in some nodes")

        # List the snapshots after glusterd restart
        # All snapshots must be listed except the one deleted
        for server in self.server_list:
            snap_list = redant.get_snap_list(server)
            if len(snap_list) != 2:
                raise Exception(f"Expected 2 snaps but got {snap_list}")
            for snap in snap_names[1:]:
                if snap not in snap_list:
                    raise Exception(f"{snap} not in {snap_list}")
