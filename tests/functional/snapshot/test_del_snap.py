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
    TC which verifies the deletion of snapshots
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
# TODO: NFS,CIFS
import traceback
from tests.d_parent_test import DParentTest


class TestDeleteSnapshotTests(DParentTest):

    def terminate(self):
        """
        Reset snapshot config options
        """
        try:
            # Disable auto-delete for snapshots
            cmd = "gluster snapshot config auto-delete disable"
            self.redant.execute_abstract_op_node(cmd, self.server_list[0])

            # Setting max-soft-limit back to 90%
            option = {'snap-max-soft-limit': '90'}
            self.redant.set_snap_config(option, self.server_list[0])

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        * Creating and deleting 10 snapshots
        * deleting previously created 10 snapshots
        * enabling auto-delete snapshot
        * Setting max-hard limit and max-soft-limit
        * Verify the limits by creating another 20 snapshots
        * Oldest of newly created snapshots will be deleted
        * Retaining the latest 8(softlimit) snapshots
        * cleanup snapshots and volumes
        """
        # creating 10 snapshots
        for snap_count in range(0, 10):
            redant.snap_create(self.vol_name, f"snap{snap_count}",
                               self.server_list[0], False,
                               "Description with $p3c1al characters!")

        # snapshot list
        redant.snap_list(self.server_list[0])

        # deleting all 10 snapshots from the volume
        redant.snap_delete_by_volumename(self.vol_name, self.server_list[0])

        # enabling auto-delete
        cmd = "gluster snapshot config auto-delete enable"
        redant.execute_abstract_op_node(cmd, self.server_list[0])

        # setting max-hard-limit
        option = {'snap-max-hard-limit': '10'}
        redant.set_snap_config(option, self.server_list[0], self.vol_name)

        # Validating max-hard-limit
        hardlimit = redant.get_snap_config(self.server_list[0], self.vol_name)
        if hardlimit['volumeConfig'][0]['hardLimit'] != '10':
            raise Exception("Failed to Validate max-hard-limit")

        # setting max-soft-limit
        option = {'snap-max-soft-limit': '80'}
        redant.set_snap_config(option, self.server_list[0])

        # Validating max-soft-limit
        softlimit = redant.get_snap_config(self.server_list[0], self.vol_name)
        if softlimit['volumeConfig'][0]['softLimit'] != '8':
            raise Exception("Failed to Validate max-soft-limit")

        # creating 20 more snapshots. As the count
        # of snapshots crosses the
        # soft-limit the oldest of newly created snapshot should
        # be deleted only latest 8(softlimit) snapshots
        # should remain
        for snap_count in range(10, 30):
            redant.snap_create(self.vol_name, f"snap{snap_count}",
                               self.server_list[0], False,
                               "Description with $p3c1al characters!")

        # snapshot list to list total number of snaps after auto-delete
        ret = redant.snap_list(self.server_list[0])
        if int(ret['msg']['snapList']['count']) != 8:
            raise Exception("Failed to validate snapshots with"
                            "expected number of snapshots")
