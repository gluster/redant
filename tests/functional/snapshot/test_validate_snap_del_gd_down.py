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
  This test cases will validate snapshot delete behaviour
  when glusterd is down on one node.

"""

# disruptive;rep
# disruptive;rep,disp,dist,dist-rep,dist-disp

from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. Create volumes
        2. Create 5 snapshots
        3. Bring one node down
        4. Delete one snapshot
        5. list snapshot and validate delete
        6. Bring up the downed node
        7. Validate number of snaps after handshake on the
           brought down node.
        """
        # Create 5 snapshot
        for i in range(0, 5):
            self.snap_name = f"{self.vol_name}-snap{i}"
            redant.snap_create(self.vol_name, self.snap_name,
                               self.server_list[0])

        # Check for no of snaps using snap_list it should be 5 now
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 5:
            raise Exception("Snap list should have 5 snap volumes. But instead"
                            f" is {snap_list}")

        # Stopping glusterd service on server[1]
        redant.stop_glusterd(self.server_list[1])
        if not redant.wait_for_glusterd_to_stop(self.server_list[1]):
            raise Exception(f"Glusterd didn't stop at {self.server_list[1]}")

        # Delete one snapshot snapy1
        self.snap_name = f"{self.vol_name}-snap1"
        redant.snap_delete(self.snap_name, self.server_list[0])

        # Check for no of snaps using snap_list it should be 4 now
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 4:
            raise Exception("Snap list should have 4 snap volumes. But instead"
                            f" is {snap_list}")
        print(snap_list)

        # Starting glusterd services on server[1]
        redant.start_glusterd(self.server_list[1])
        if not redant.wait_for_glusterd_to_start(self.server_list[1]):
            raise Exception(f"Glusterd didn't start at {self.server_list[1]}")

        # Wait till peers are in connected mode.
        if not redant.wait_till_all_peers_connected(self.server_list):
            raise Exception("Peers are not in connected state.")

        # Check for no of snaps using snap_list it should be 4 now
        for _ in range(60):
            snap_list = redant.get_snap_list(self.server_list[1],
                                             self.vol_name)
            if len(snap_list) == 4:
                 break
            sleep(5)
        if len(snap_list) != 4:
            raise Exception("Snap list should have 4 snap volumes. But instead"
                            f" is {snap_list}")
