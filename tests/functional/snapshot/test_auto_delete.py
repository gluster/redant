"""
Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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

Description: Tests which verifies the deletion of snapshots along
with the snapshot config option 'auto-delete'
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;rep,dist-rep,disp,dist-disp,dist


class TestCase(DParentTest):
    """
    Tests which verifies the deletion of snapshots along
    with the snapshot config option 'auto-delete'
    """

    def terminate(self):
        try:
            # Reset the softlimit.
            self.redant.set_snap_config(self.def_soft_lim, self.server_list[0])

            # Disable auto-delete.
            autodel_disable = {"auto-delete": "disable"}
            self.redant.set_snap_config(autodel_disable, self.server_list[0])
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Verifying snapshot auto-delete config option

        * Enable auto-delete snapshot
        * Set snap-max-hard limit and snap-max-soft-limit
        * Validate snap-max-hard-limit and snap-max-soft-limit
        * Verify the limits by creating another 20 snapshots
        * Oldest of newly created snapshots will be deleted
        * Retaining the latest 8 (softlimit) snapshots
        """

        default_conf = redant.get_snap_config(self.server_list[0])
        self.def_soft_lim = {"snap-max-soft-limit":
                             default_conf['systemConfig']['softLimit'][:-1]}

        # Enable auto-delete snapshot config option
        autodel_enable = {"auto-delete": "enable"}
        redant.set_snap_config(autodel_enable, self.server_list[0])

        # Set snap-max-hard-limit snapshot config option for volume
        max_hard_limit = {'snap-max-hard-limit': '10'}
        redant.set_snap_config(max_hard_limit, self.server_list[0],
                               self.vol_name)

        # Validate snap-max-hard-limit snapshot config option
        config_v = redant.get_snap_config(self.server_list[0],
                                          self.vol_name)
        if config_v['volumeConfig'][0]['hardLimit'] != '10':
            raise Exception("Expected hardlimit of 10 but got "
                            f" {config_v['volumeConfig'][0]['hardLimit']} for"
                            f" when queried for volume {self.vol_name}")

        # Set snap-max-soft-limit snapshot config option
        max_soft_limit = {'snap-max-soft-limit': '80'}
        redant.set_snap_config(max_soft_limit, self.server_list[0])

        # Validate snap-max-soft-limit snapshot config option
        config_v = redant.get_snap_config(self.server_list[0],
                                          self.vol_name)
        if config_v['volumeConfig'][0]['softLimit'] != '8':
            raise Exception("Expected softlimit of 8 but got"
                            f" {config_v['volumeConfig'][0]['softLimit']} for"
                            f" when queried for volume {self.vol_name}")

        self.snapshots = [f"{self.vol_name}-snap{i}" for i in range(20)]

        # Create 20 snapshots. As the count of snapshots crosses the
        # soft-limit the oldest of newly created snapshot should
        # be deleted and only the latest 8 snapshots must remain.
        for snapname in self.snapshots:
            redant.snap_create(self.vol_name, snapname, self.server_list[0],
                               description="This is the Description wit#"
                                           " ($p3c1al) ch@r@cters!")

        # Perform snapshot list to get total number of snaps after auto-delete
        # Validate the existence of the snapshots using the snapname
        snaplist = redant.get_snap_list(self.server_list[0])
        for snapname in self.snapshots[-8:]:
            if snapname not in snaplist:
                raise Exception(f"{snapname} is expected to be in the"
                                " snap list")
