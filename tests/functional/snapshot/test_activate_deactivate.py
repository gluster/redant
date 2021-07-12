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
    Verifying snapshot activation and deactivation functionality
as well as snap info and status output.
"""


from tests.d_parent_test import DParentTest

# disruptive;rep,dist,dist-rep,disp,dist-disp


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Verifying Snapshot activation/deactivation functionality.

        * Create Snapshot
        * Validate snapshot info before activation
        * Validate snapshot status before activation
        * Activate snapshot
        * Validate snapshot info after activation
        * Validate snapshot status after activation
        * Deactivate snapshot
        * Validate snapshot info after deactivation
        * Validate snapshot status after deactivation
        """

        # Create Snapshot
        snap_name = f"{self.vol_name}-snap"
        redant.snap_create(self.vol_name, snap_name, self.server_list[0])

        # Validate Snapshot Info Before Activation
        ret = redant.get_snap_info_by_snapname(snap_name, self.server_list[0])
        if ret is None:
            raise Exception(f"Snap info for {snap_name} not found")
        if ret['snapVolume']['status'] != 'Stopped':
            raise Exception("Snap status should be stopped before activation.")

        # Validate Snapshot Status Before Activation
        ret = redant.get_snap_status_by_snapname(snap_name,
                                                 self.server_list[0])
        for brick in ret['volume']['brick']:
            if brick['pid'] != 'N/A':
                raise Exception("Unexpected. Brick pid available for the brick"
                                f" {brick['path']} as {brick['pid']}")

        # Activate Snapshot
        redant.snap_activate(snap_name, self.server_list[0])

        # Validate Snapshot Info After Activation
        ret = redant.get_snap_info_by_snapname(snap_name, self.server_list[0])
        if ret is None:
            raise Exception(f"Snap info for {snap_name} not found")
        if ret['snapVolume']['status'] == 'Stopped':
            raise Exception("Snap status shouldn't be stopped after"
                            " activation.")

        # Validate Snaphot Status After Activation
        ret = redant.get_snap_status_by_snapname(snap_name,
                                                 self.server_list[0])
        for brick in ret['volume']['brick']:
            if brick['pid'] == 'N/A':
                raise Exception(f"Unexpected. Brick pid for {brick['path']}"
                                " shouldn't be N/A")

        # Deactivate Snapshot
        redant.snap_deactivate(snap_name, self.server_list[0])

        # Validate Snapshot Info After Deactivation
        ret = redant.get_snap_info_by_snapname(snap_name, self.server_list[0])
        if ret is None:
            raise Exception(f"Snap info for {snap_name} not found")
        if ret['snapVolume']['status'] != 'Stopped':
            raise Exception("Snap status should be stopped after"
                            " de-activation.")

        # Validate Snaphot Status After Deactivation
        ret = redant.get_snap_status_by_snapname(snap_name,
                                                 self.server_list[0])
        for brick in ret['volume']['brick']:
            if brick['pid'] != 'N/A':
                raise Exception("Unexpected. Brick pid available for the brick"
                                f" {brick['path']} as {brick['pid']}")
