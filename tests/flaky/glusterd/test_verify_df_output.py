"""
 Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>
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
    Test to verufy the df -h value for various brick and volume
    operations.

*Flaky Test*
Reason: Calculation of disk size is failing in CI for disp* volume,
        as the size of disks are in TB.
"""

# disruptive;disp,dist-disp
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def _perform_io_and_validate(self):
        """ Performs IO on the mount points and validates it"""
        self.mounts = (self.redant.es.
                       get_mnt_pts_dict_in_list(self.vol_name))
        self.all_mounts_procs, counter = [], 1

        for mount in self.mounts:
            self.redant.logger.info(f"Starting IO on {mount['client']}:"
                                    f"{mount['mountpath']}")
            proc = self.redant.create_deep_dirs_with_files(mount['mountpath'],
                                                           counter, 2, 3, 3, 2,
                                                           mount['client'])
            self.all_mounts_procs.append(proc)
            counter = counter + 10

        # Validating IO's on mount point and waiting to complete
        ret = self.redant.validate_io_procs(self.all_mounts_procs,
                                            self.mounts)
        if not ret:
            raise Exception("IO validation failed")

    def _replace_bricks_and_wait_for_heal_completion(self):
        """ Replaces all the bricks and waits for the heal to complete"""
        existing_bricks = self.redant.get_all_bricks(self.vol_name,
                                                     self.server_list[0])
        if existing_bricks is None:
            raise Exception("Failed to get the bricks list")

        for brick_to_replace in existing_bricks:
            ret = (self.redant.
                   replace_brick_from_volume(self.vol_name,
                                             self.server_list[0],
                                             self.server_list,
                                             src_brick=brick_to_replace,
                                             brick_roots=self.brick_roots))
            if not ret:
                raise Exception(f"Replace of {brick_to_replace} failed")

            # Monitor heal completion
            if not (self.redant.
                    monitor_heal_completion(self.server_list[0],
                                            self.vol_name)):
                raise Exception("Heal has not yet completed")

    def _get_mount_size_from_df_h_output(self):
        """ Extracts the mount size from the df -h output"""

        split_cmd = " | awk '{split($0,a,\" \");print a[2]}' | sed 's/.$//'"
        cmd = (f"cd {self.mounts[0]['mountpath']}; df -h | grep "
               f"{self.vol_name} {split_cmd}")
        ret = self.redant.execute_abstract_op_node(cmd, self.client_list[0])
        return float(ret['msg'][0].split("\n")[0])

    def run_test(self, redant):
        """
        - Take the output of df -h.
        - Replace any one brick for the volumes.
        - Wait till the heal is completed
        - Repeat steps 1, 2 and 3 for all bricks for all volumes.
        - Check if there are any inconsistencies in the output of df -h
        - Remove bricks from volume and check output of df -h
        - Add bricks to volume and check output of df -h
        """
        # Check hardware configuration
        if (self.volume_type == "dist-arb" or self.volume_type == "dist-rep"
           or self.volume_type == "dist-disp"):
            redant.check_hardware_requirements(self.server_list, 6,
                                               self.brick_roots, 2)
        else:
            redant.check_hardware_requirements(self.server_list, 3,
                                               self.brick_roots, 2)

        # Perform some IO on the mount point
        self._perform_io_and_validate()

        # Get the mount size from df -h output
        initial_mount_size = self._get_mount_size_from_df_h_output()

        # Replace all the bricks and wait till the heal completes
        self._replace_bricks_and_wait_for_heal_completion()

        # Get df -h output after brick replace
        mount_size_after_replace = self._get_mount_size_from_df_h_output()
        # Verify the mount point size remains the same after brick replace
        if initial_mount_size != mount_size_after_replace:
            raise Exception("The mount sizes before and after replace bricks "
                            "are not same")

        # Add bricks
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots, True)

        if not ret:
            raise Exception("Failed to expand volume")

        # Get df -h output after volume expand
        mount_size_after_expand = self._get_mount_size_from_df_h_output()

        # Verify df -h output returns greater value
        if mount_size_after_expand <= initial_mount_size:
            raise Exception("The mount size has not increased after expanding")

        # Remove bricks
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   force=True)

        if not ret:
            raise Exception("Failed to shrink volume")

        # Get df -h output after volume shrink
        mount_size_after_shrink = self._get_mount_size_from_df_h_output()

        # Verify the df -h output returns smaller value
        if mount_size_after_expand <= mount_size_after_shrink:
            raise Exception("The mount size has not reduced after shrinking")
