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
    TC to check removal of faulty subvol and adding a new subvol
"""

# disruptive;dist-arb
# TODO: NFS,CIFS
from tests.d_parent_test import DParentTest


class TestArbiterSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        - Create an distribute-replicate arbiter volume
        - Create IO
        - Calculate areequal
        - Remove a subvolume
        - Calculate areequal and compare with previous
        - Expand the volume
        - Do rebalance and check status
        - Calculate areequal and compare with previous
        """
        # Creating files on client side
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        counter = 0
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      counter, 2, 2, 2, 20,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            counter += 10

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Get arequal before removing subvol
        result_bfre_remove_subvol = redant.collect_mounts_arequal(self.mounts)

        # Remove subvol
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   subvol_num=1)
        if not ret:
            raise Exception("Failed to remove subvolume")

        # Get areequal after removing subvol
        result_aftr_remove_subvol = redant.collect_mounts_arequal(self.mounts)

        # Comparing areequal before removing subvol
        # and after removing subvol
        if result_bfre_remove_subvol != result_aftr_remove_subvol:
            raise Exception("Arequals before removing subvol and "
                            "after removing subvol are not equal")

        # Expand volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception("Failed to exapnd volume")

        # Log Volume Info and Status after expanding the volume
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.volname}")

        # Do rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        if not redant.wait_for_rebalance_to_complete(self.vol_name,
                                                     self.server_list[0]):
            raise Exception("Rebalance is not completed")

        # Get arequal after expanding volume
        result_aftr_expand_volume = redant.collect_mounts_arequal(self.mounts)

        # Comparing areequal before removing subvol
        # and after expanding volume
        if result_aftr_expand_volume != result_bfre_remove_subvol:
            raise Exception("Areequals before removing subvol and "
                            "after expanding volume are not equal")
