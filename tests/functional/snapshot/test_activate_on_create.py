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
    Verufying snapshot activate-on-create.
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;rep,dist,dist-rep,disp,dist-disp


class TestCase(DParentTest):

    def terminate(self):
        try:
            if self.option_enabled:
                option_disable = {'activate-on-create': 'disable'}
                self.redant.set_snap_config(option_disable,
                                            self.server_list[0])
            else:
                print("Option reset!")
        except Exception as e:
            tb = traceback.format_exc()
            self.redant.logger.error(e)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Verifying Snapshot activate on create

        * Create a default snapshot
        * Enable activate-on-create snapshot config option
        * Create more snapshots
            * Validate snapshot info after snapshot create. It should be in
              started state.
            * Validate snapshot status after snapshot create. It should be in
              started state.
        * Validate the default snapshot info and status. It should be in
          stopped state
        """
        self.option_enabled = False
        # Create Default Snapshot
        snap_default = f"{self.vol_name}-snap"
        redant.snap_create(self.vol_name, snap_default, self.server_list[0])

        # Enable activate_on_create snapshot
        option_enable = {'activate-on-create': 'enable'}
        redant.set_snap_config(option_enable, self.server_list[0])
        ret = redant.get_snap_config(self.server_list[0], self.vol_name)
        if ret['systemConfig']['activateOnCreate'] != 'enable':
            raise Exception(f'Activate on create not enabled. Got {ret}')
        self.option_enabled = True

        # Create Snapshots after enabling activate-on-create
        for snap_count in range(1, 5):
            snap_name = f"{self.vol_name}-snap{snap_count}"
            redant.snap_create(self.vol_name, snap_name, self.server_list[0])

            # Validate Snapshot Info After Snapshot Create
            ret = redant.get_snap_info_by_snapname(snap_name,
                                                   self.server_list[0])
            if not ret:
                raise Exception(f"Snap info fetch for {snap_name} failed.")

            if ret['snapVolume']['status'] != 'Started':
                raise Exception(f"Snap {snap_name} is not started.")

            # Validate Snaphot Status After Snapshot Create
            ret = redant.get_snap_status_by_snapname(snap_name,
                                                     self.server_list[0])
            if not ret:
                raise Exception(f"Snap status fetch failed for {snap_name}")
            for brick_val in ret['volume']['brick']:
                if brick_val['pid'] == "N/A":
                    raise Exception(f"Brick {brick_val} of {snap_name} is "
                                    "offline")

        # Validate Snapshot Info for the 'default' snapshot
        # Expected to be Stopped
        ret = redant.get_snap_info_by_snapname(snap_default,
                                               self.server_list[0])
        if not ret:
            raise Exception(f"Snap info fetch failed for {snap_name}")

        if ret['snapVolume']['status'] == 'Started':
            raise Exception(f"Snap {snap_default} shouldn't be"
                            " in Started mode.")

        # Validate Snapshot Status for the 'default' snapshot
        # Expected to be N/A
        ret = redant.get_snap_status_by_snapname(snap_default,
                                                 self.server_list[0])
        if not ret:
            raise Exception(f"Snap status fetch failed for {snap_default}")

        if brick_val in ret['volume']['brick']:
            if brick_val['pid'] != "N/A":
                raise Exception(f"Brick {brick_val} of {snap_default} is "
                                "online")
