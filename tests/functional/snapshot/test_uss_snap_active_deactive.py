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
    This test case will validate USS functionality.
    Activated snaps should get listed in .snap directory while deactivated
    snap should not.
"""

# disruptive;rep,dist,disp,dist-rep,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
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
        * Create volume
        * Mount volume
        * Perform I/O on mounts
        * Create 2 snapshots.
        * Validate snap created
        * Enable USS
        * Validate USS is enabled
        * Validate snapd is running
        * Activate the snapshots.
        * List snaps under .snap directory
          -- previously created snaps should be listed under .snaps
        * Deactivate one of the snapshot
        * List snaps under .snap directory
          -- snapshot is not listed as it is deactivated
        * Activate the deactivated snapshot
        * List snaps under .snap directory
          -- both snapshots should be listed under .snaps
        """
        # Perform I/O
        redant.logger.info("Starting IO on all mounts...")
        counter = 1
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for mount in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 3, 3, 10,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter += 10

        # Wait till IO finishes.
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed")

        # Enable USS
        redant.enable_uss(self.vol_name, self.server_list[0])

        # Validate USS is enabled
        if not redant.is_uss_enabled(self.vol_name, self.server_list[0]):
            raise Exception("USS is not enabled.")

        # Validate snapd running
        for server in self.server_list:
            if not redant.is_snapd_running(self.vol_name, server):
                raise Exception(f"Snapd not running in {server}")

        # Create 2 snapshot
        for i in range(1, 3):
            snap_name = f"{self.vol_name}-snap{i}"
            redant.snap_create(self.vol_name, snap_name,
                               self.server_list[0])

        # Check for no of snaps using snap_list it should be 2 now
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 2:
            raise Exception("Snap list should have 2 snap volumes. But instead"
                            f" is {snap_list}")

        # Activate snapshots
        for i in range(1, 3):
            snap_name = f"{self.vol_name}-snap{i}"
            redant.snap_activate(snap_name, self.server_list[0])

        # list activated snapshots directory under .snaps
        if not redant.view_snaps_from_mount(self.mounts, snap_list):
            raise Exception("Snap in .snaps doesn't match snap list provided")

        # Deactivate the second snapshot
        redant.snap_deactivate(snap_list[1], self.server_list[0])

        # validate the given snap is absent in mountpoint
        if redant.view_snaps_from_mount(self.mounts, snap_list[1], False):
            raise Exception(f"Snap {snap_list[1]} shouldn't be present under"
                            ".snaps dir")

        # Activate snapshot the second snapshot
        redant.snap_activate(snap_list[1], self.server_list[0])

        # list activated snapshots directory under .snaps
        if not redant.view_snaps_from_mount(self.mounts, snap_list):
            raise Exception("Snap in .snaps doesn't match snap list provided")
