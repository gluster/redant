"""
 Copyright (C) 2017-2021 Red Hat, Inc. <http://www.redhat.com>

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
    Positive test - Exercise Add-brick command
"""

# disruptive;dist,rep,disp,dist-rep,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestExerciseAddbrickCommand(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 self.vol_type_inf[self.volume_type],
                                 self.server_list, self.brick_roots)

    def terminate(self):
        """
        Wait for IO toc omplete, if the TC fails early
        """
        try:
            if self.is_io_running:
                if not self.redant.wait_for_io_to_complete(self.io_process,
                                                           self.mounts):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        - Create and start a volume
        - Expand volume, it should be a success
        - Expand volume again, it should be a success
        """
        self.is_io_running = False

        # Add brick to running volume
        vol_bricks_before = redant.get_all_bricks(self.vol_name,
                                                  self.server_list[0])

        force = False
        if self.volume_type == "dist-disp" or self.volume_type == "disp":
            force = True

        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=force)
        if not ret:
            raise Exception("Failed to expand volume")

        vol_bricks_after = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])

        if len(vol_bricks_after) <= len(vol_bricks_before):
            raise Exception("Expected new volume size to be greater than old")

        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=force)
        if not ret:
            raise Exception("Failed ot expand volume")

        vol_bricks_before = vol_bricks_after
        vol_bricks_after = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])

        if len(vol_bricks_after) <= len(vol_bricks_before):
            raise Exception("Expected new volume size to be greater than old")

        # Reset volume config
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   subvol_num=2, force=True)
        if not ret:
            raise Exception("Shrinking volume to old config failed")

        # Case 2: def test_add_bricks_stopped_volume
        """
        Steps:
        - Create and start a volume
        - Stop the volume
        - Expand volume again, it should be a success
        """
        redant.volume_stop(self.vol_name, self.server_list[0])

        vol_bricks_before = redant.get_all_bricks(self.vol_name,
                                                  self.server_list[0])

        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=force)
        if not ret:
            raise Exception("Failed ot expand volume")

        vol_bricks_after = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        if len(vol_bricks_after) <= len(vol_bricks_before):
            raise Exception("Expected new volume size to be greater than old")

        # Reset volume config
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   subvol_num=1, force=True)
        if not ret:
            raise Exception("Shrinking volume to old config failed")

        # Case 3: def test_add_bricks_io_mount_point
        """
        Test Case Steps:
        1. Create, start and mount volume.
        2. Start I/O on volume.
        3. Add brick and start rebalance on the volume.
        4. Wait for rebalance to complete.
        5. Check for I/O failures if any.
        """
        # Mount volume
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

        # Start IO on mounts
        self.io_process = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for index, mount_obj in enumerate(self.mounts, start=1):
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      index + 10, 2, 2, 2, 10,
                                                      mount_obj['client'])
            self.io_process.append(proc)
            self.is_io_running = True

        # Expand volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=force)
        if not ret:
            raise Exception("Failed ot expand volume")

        # Validate IO on current mount point
        ret = redant.validate_io_procs(self.io_process, self.mounts)
        if not ret:
            raise Exception('IO Failed on clients')
        self.is_io_running = False

        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])
        redant.execute_abstract_op_node(f"rm -rf {self.mountpoint}",
                                        self.client_list[0])
