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
    This test case will validate USS behaviour when we
    enable USS on the volume when brick is down.
"""

# disruptive;rep,dist-rep,disp,dist,dist-disp
# TODO NFS and CIFS

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
        * Bring down one brick
        * Enable USS
        * Validate USS is enabled
        * Bring the brick online using gluster v start force
        * Create 2 snapshots.
        * Validate snap created
        * Activate both the snapshots.
        * Validate whether both the snapshots are listed under .snaps
        """

        # Perform I/O
        redant.logger.info("Starting IO on all mounts...")
        counter = 1
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 3, 4, 10,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter += 10

        # Check async command status.
        for async_job in self.all_mounts_procs:
            if redant.check_async_command_status(async_job):
                raise Exception("IO shouldn't have ended.")

        # Bring down 1 brick from brick list
        bricks_list = redant.get_online_bricks_list(self.vol_name,
                                                    self.server_list[0])
        redant.bring_bricks_offline(self.vol_name, [bricks_list[1]])
        if not redant.are_bricks_offline(self.vol_name,
                                         [bricks_list[1]],
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_list[1]} is not offline")

        # Enable USS
        redant.enable_uss(self.vol_name, self.server_list[0])

        # Validate USS is enabled
        if not redant.is_uss_enabled(self.vol_name, self.server_list[0]):
            raise Exception("USS is not enabled.")

        #  Bring the brick online using gluster v start force
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          bricks_list[1]):
            raise Exception(f"Couldn't bring {bricks_list[1]} online")

        # Create 2 snapshot
        for i in range(0, 2):
            snap_name = f"{self.vol_name}-snap{i}"
            redant.snap_create(self.vol_name, snap_name,
                               self.server_list[0])

        # Check for no of snaps using snap_list it should be 2 now
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 2:
            raise Exception("Snap list should have 2 snap volumes. But instead"
                            f" is {snap_list}")

        # Activate the snapshots
        for i in range(0, 2):
            snap_name = f"{self.vol_name}-snap{i}"
            redant.snap_activate(snap_name, self.server_list[0])

        # Validate if all snaps are listed under .snaps
        if not redant.view_snap_from_mount(self.mounts, snap_list):
            raise Exception("Snap in .snaps doesn't match snap list provided")
