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
uss functionality while io is going on.

"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;rep,dist,disp,dist-rep,dist-disp


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_proc,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")
        except Exception as e:
            tb = traceback.format_exc()
            self.redant.logger.error(e)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1. Create volume
        2. enable uss on created volume
        3. validate uss running
        4. validate snapd running on all nodes
        5. perform io on mounts
        6. create 10 snapshots with description
        7. validate with snapshot list
        8. validate io is completed
        9. Activate snapshots to list all snaps
           under .snaps
        10. validate snapshots under .snaps directory
        """
        # Enable USS
        redant.enable_uss(self.vol_name, self.server_list[0])

        # Validate USS running
        if not redant.is_uss_enabled(self.vol_name, self.server_list[0]):
            raise Exception(f"USS is not enabled in {self.server_list[0]}")

        # Validate snapd running
        for server in self.server_list:
            if not redant.is_snapd_running(self.vol_name, server):
                raise Exception(f"Snapd is not running in {server}")

        # Perform I/O
        self.all_mounts_proc = []
        counter = 1
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for mount in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 3, 4, 10,
                                                      mount['client'])
            self.all_mounts_proc.append(proc)
            counter += 10

        # Creating snapshot with description
        for count in range(0, 10):
            snap_name = f"{self.vol_name}-snap{count}"
            desc = '$p3C!@l C#@R@cT#R$'
            redant.snap_create(self.vol_name, snap_name, self.server_list[0],
                               description=desc)

        # Validate snapshot list
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 10:
            raise Exception(f"Expected 10 snapshots but got {snap_list}")

        # Activating snapshot
        for count in range(0, 10):
            snap_name = f"{self.vol_name}-snap{count}"
            redant.snap_activate(snap_name, self.server_list[0])

        # Validate IO is completed
        if not redant.validate_io_procs(self.all_mounts_proc, self.mounts):
            raise Exception("IO failed")

        # validate snapshots are listed under .snaps directory
        if not redant.view_snap_from_mount(self.mounts, snap_list):
            raise Exception("Snap in .snaps doesn't match snap list provided")
