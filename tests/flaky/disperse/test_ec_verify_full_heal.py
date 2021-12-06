"""
 Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to verify full-heal

 *Flaky Test*
 Reason: Triggering heal is failing
"""

# nonDisruptive;disp
from tests.nd_parent_test import NdParentTest


class TestHealFull(NdParentTest):

    def run_test(self, redant):
        """
        - Create IO
        - Calculate arequal from mount
        - Delete data from backend from the EC volume
        - Trigger heal full
        - Check if heal is completed
        - Calculate arequal checksum and compare it
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        count = 1
        # Creating files on client side
        for mount_obj in self.mounts:
            # Create dirs with file
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 2, 2, 20,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count = count + 10

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs,
                                       self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Get areequal before deleting the files from brick
        result_before_klng_procs = redant.collect_mounts_arequal(self.mounts)

        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols list")

        # Delete data from backend from the erasure node
        for subvol in subvols:
            erasure = subvol[-1]
            node, brick_path = erasure.split(':')
            redant.execute_abstract_op_node(f"cd {brick_path}/ ; rm -rf *",
                                            node)

        # Trigger heal full
        if not redant.trigger_heal_full(self.vol_name, self.server_list[0]):
            raise Exception("Failed to trigger full-heal")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name,):
            raise Exception("Heal not completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception('Heal is not complete')

        # Get areequal after healing
        result_after_healing = redant.collect_mounts_arequal(self.mounts)

        # Comparing areequals
        if result_before_klng_procs != result_after_healing:
            raise Exception('Arequals before before clearing data '
                            'and after healing are not equal')
