"""
  Copyright (C) 2017-2020 Red Hat, Inc. <http://www.redhat.com>

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
snapshot activation and deactivation status
when glusterd is down.
"""

# disruptive;rep,dist,disp,dist-rep,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Steps:

        1. create a volume
        2. mount volume
        3. create snapshot of that volume
        4. validate using snapshot info
        5. Activate snapshot
        6. List all snapshots present
        7. validate using snapshot info
        8. Stop glusterd on one node
        9. Check glusterd status
       10. deactivate created snapshot
       11. Start glusterd on that node
       12. Check glusterd status
       13. validate using snapshot info
       13. Check all peers are connected

        """
        # Creating snapshot:
        snap_name = f"{self.vol_name}-snap"
        redant.snap_create(self.vol_name, snap_name, self.server_list[0])

        # Check snapshot info
        ret = redant.get_snap_info_by_snapname(snap_name, self.server_list[0])
        if ret is None:
            raise Exception(f"Snap info for {snap_name} not found")
        if ret['snapVolume']['status'] != 'Stopped':
            raise Exception("Snap status should be stopped before activation.")

        # Activating snapshot
        redant.snap_activate(snap_name, self.server_list[0])

        # snapshot list
        ret = redant.get_snap_list(self.server_list[0])
        if len(ret) > 1:
            raise Exception("More than 1 snapshot present even though only 1"
                            " was created")

        # Check snapshot info
        ret = redant.get_snap_info_by_snapname(snap_name, self.server_list[0])
        if ret is None:
            raise Exception(f"Snap info for {snap_name} not found")
        if ret['snapVolume']['status'] != 'Started':
            raise Exception("Snap status should be started after activation.")

        # Stop Glusterd on one node
        redant.stop_glusterd(self.server_list[1])
        if not redant.wait_for_glusterd_to_stop(self.server_list[1]):
            raise Exception(f"Glusterd didn't stop at {self.server_list[1]}")

        # de-activating snapshot
        redant.snap_deactivate(snap_name, self.server_list[0])

        # validate snapshot info
        ret = redant.get_snap_info_by_snapname(snap_name, self.server_list[0])
        if ret is None:
            raise Exception(f"Snap info for {snap_name} not found")
        if ret['snapVolume']['status'] != 'Stopped':
            raise Exception("Snap status should be stopped before activation.")

        # Start Glusterd on node
        redant.start_glusterd(self.server_list[1])
        if not redant.wait_for_glusterd_to_start(self.server_list[1]):
            raise Exception(f"Glusterd didn't start at {self.server_list[1]}")

        # validate snapshot info
        ret = redant.get_snap_info_by_snapname(snap_name, self.server_list[0])
        if ret is None:
            raise Exception(f"Snap info for {snap_name} not found")
        if ret['snapVolume']['status'] != 'Stopped':
            raise Exception("Snap status should be stopped after"
                            "deactivation.")
