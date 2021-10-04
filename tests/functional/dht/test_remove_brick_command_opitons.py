"""
Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along`
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# disruptive;dist-rep,dist-arb,dist-disp,dist
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestRemoveBrickCommandOptions(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 3
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _run_io_on_mount_point(self, fname="file"):
        """Create a few files on mount point"""
        cmd = (f"cd {self.mountpoint};for i in `seq 1 5`; do mkdir dir$i;"
               f"for j in `seq 1 10`; do touch {fname}$j ;done;done")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _test_remove_brick_command_basic(self):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create some data on the volume.
        3. Run remove-brick start, status and finally commit.
        4. Check if there is any data loss or not.
        """
        # Create some data on the volume
        self._run_io_on_mount_point()

        # Collect arequal checksum before ops
        arequal_before = self.redant.collect_mounts_arequal(self.mounts)

        # Run remove-brick start, status and finally commit
        ret = self.redant.shrink_volume(self.server_list[0], self.vol_name)
        if not ret:
            raise Exception("Failed to remove-brick from volume")

        # Check for data loss by comparing arequal before and after ops
        arequal_after = self.redant.collect_mounts_arequal(self.mounts)

        if arequal_before != arequal_after:
            raise Exception("arequal checksum is NOT MATCHNG")

    def _test_remove_brick_command_force(self):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create some data on the volume.
        3. Run remove-brick with force.
        4. Check if bricks are still seen on volume or not
        """
        # Create some data on the volume
        self._run_io_on_mount_point()

        # Remove-brick on the volume with force option
        brick_list_to_remove = (self.redant.form_bricks_list_to_remove_brick(
                                self.server_list[0], self.vol_name))
        if brick_list_to_remove is None:
            raise Exception(f"Volume {self.vol_name}: Failed to form bricks"
                            " list for shrink")

        self.redant.remove_brick(self.server_list[0], self.vol_name,
                                 brick_list_to_remove, "force")

        # Get a list of all bricks
        brick_list = self.redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])

        # Check if bricks removed brick are present or not in brick list
        for brick in brick_list_to_remove:
            if brick in brick_list:
                raise Exception("Brick still present in brick list even "
                                "after removing")

    def run_test(self, redant):
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        self._test_remove_brick_command_basic()
        redant.logger.info("remove-brick start, status and commit success")
        self._test_remove_brick_command_force()
        redant.logger.info("remove-brick with force success")
