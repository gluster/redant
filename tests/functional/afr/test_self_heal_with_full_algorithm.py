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
    Test self heal when data-self-heal-algorithm option is set to full.
"""

# disruptive;arb,dist-arb,rep,dist-rep
from tests.d_parent_test import DParentTest


class TestSelfHealWithFullAlgorithm(DParentTest):

    def _check_full_data_heal(self, brick_set):
        """
        Bring specified set of bricks in each subvolume offline, pump I/O,
        bring the bricks online, wait for heal and check arequal.
        """
        bricks_to_bring_offline = []
        subvols = self.redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")
        bricks_list = zip(*subvols)

        bricks_to_bring_offline = list(list(bricks_list)[brick_set])

        if not self.redant.bring_bricks_offline(self.vol_name,
                                                bricks_to_bring_offline):
            raise Exception("Unable to bring brick: "
                            f"{bricks_to_bring_offline} offline")

        # Validate the bricks are offline
        if not self.redant.are_bricks_offline(self.vol_name,
                                              bricks_to_bring_offline,
                                              self.server_list[0]):
            raise Exception(f"Brick:{bricks_to_bring_offline} is still "
                            "online")

        if brick_set == 0:
            # Create few files under the directory with data
            cmd = (f"cd {self.mountpoint}/test_full_self_heal; "
                   "for i in `seq 1 100` ; do dd if=/dev/urandom of=file.$i "
                   "bs=1M count=1; done;")
        else:
            # Modify files under test_full_self_heal directory
            cmd = (f"cd {self.mountpoint}/test_full_self_heal; "
                   "for i in `seq 1 100` ; do truncate -s 0 file.$i ; "
                   "truncate -s 2M file.$i ; done;")

        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Start volume with force to bring all bricks online
        self.redant.volume_start(self.vol_name, self.server_list[0],
                                 force=True)

        # Verify volume's all process are online
        if not (self.redant.verify_all_process_of_volume_are_online(
                self.vol_name, self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Monitor heal completion
        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name,
                                                   interval_check=10):
            raise Exception("Heal is not yet completed")

        # Check are there any files in split-brain
        if self.redant.is_volume_in_split_brain(self.server_list[0],
                                                self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Check arequal checksum of all the bricks are same
        for subvol in subvols:
            new_arequal = []
            arequal_from_the_bricks = \
                self.redant.collect_bricks_arequal(subvol)
            for item in arequal_from_the_bricks:
                item = " ".join(item)
                new_arequal.append(item)

            val = len(set(new_arequal))
            if (self.volume_type == "arb" or self.volume_type == "dist-arb"):
                val = len(set(new_arequal[:2]))
            if val != 1:
                raise Exception("Arequal is not same on all the bricks in the"
                                " subvol")

    def run_test(self, redant):
        """
        Test Steps:
        1. Create a replicated/distributed-replicate volume and mount it
        2. Set data/metadata/entry-self-heal to off and
           data-self-heal-algorithm to full
        3. Create a directory from the mount point
        4. Bring down all bricks from a selected set
        5. Create few files inside the directory with some data
        6. Bring back the bricks online and wait for heal to complete
        7. Check arequal of the subvol and all the bricks in the subvol should
           have same checksum
        8. Bring down all bricks from another set
        9. Modify the data of existing files under the directory
        10. Bring back the bricks online and wait for heal to complete
        11. Check arequal of the subvol and all the brick in the same subvol
            should have same checksum
        """

        # Setting options
        options = {
            "data-self-heal": "off",
            "metadata-self-heal": "off",
            "entry-self-heal": "off",
            "data-self-heal-algorithm": "full"
        }
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        redant.create_dir(self.mountpoint, "test_full_self_heal",
                          self.client_list[0])

        # Test full data heal
        self._check_full_data_heal(0)
        self._check_full_data_heal(1)
