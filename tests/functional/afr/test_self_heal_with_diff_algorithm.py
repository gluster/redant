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

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    Test self heal when data-self-heal-algorithm option is set to diff.
"""

# disruptive;arb,dist-arb,rep,dist-rep
from random import sample
from tests.d_parent_test import DParentTest


class TestSelfHealWithDiffAlgorithm(DParentTest):

    def run_test(self, redant):
        """
        Test Steps:
        1. Create a replicated/distributed-replicate volume and mount it
        2. Set data/metadata/entry-self-heal to off and
           data-self-heal-algorithm to diff
        3. Create few files inside a directory with some data
        4. Check arequal of the subvol and all the bricks in the subvol should
           have same checksum
        5. Bring down a brick from the subvol and validate it is offline
        6. Modify the data of existing files under the directory
        7. Bring back the brick online and wait for heal to complete
        8. Check arequal of the subvol and all the brick in the same subvol
           should have same checksum
        """

        # Setting options
        options = {
            "data-self-heal": "off",
            "metadata-self-heal": "off",
            "entry-self-heal": "off",
            "data-self-heal-algorithm": "diff"
        }
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Create few files under a directory with data
        cmd = (f"mkdir {self.mountpoint}/test_diff_self_heal; "
               f"cd {self.mountpoint}/test_diff_self_heal;"
               "for i in `seq 1 100` ; do dd if=/dev/urandom of=file.$i "
               "bs=1M count=1; done;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check arequal checksum of all the bricks is same
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")

        for subvol in subvols:
            new_arequal = []
            arequal_from_the_bricks = redant.collect_bricks_arequal(subvol)
            for item in arequal_from_the_bricks:
                item = " ".join(item)
                new_arequal.append(item)

            val = len(set(new_arequal))
            if (self.volume_type == "arb" or self.volume_type == "dist-arb"):
                val = len(set(new_arequal[:2]))
            if val != 1:
                raise Exception("Arequal is not same on all the bricks in the"
                                " subvol")

        # List a brick in each subvol and bring them offline
        brick_to_bring_offline = []
        for subvol in subvols:
            brick_to_bring_offline.extend(sample(subvol, 1))

        if not redant.bring_bricks_offline(self.vol_name,
                                           brick_to_bring_offline):
            raise Exception(f"Unable to bring brick {brick_to_bring_offline}"
                            " offline")

        # Validate the brick is offline
        if not redant.are_bricks_offline(self.vol_name,
                                         brick_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Brick:{brick_to_bring_offline} is still online")

        # Modify files under test_diff_self_heal directory
        cmd = (f"cd {self.mountpoint}/test_diff_self_heal; "
               "for i in `seq 1 100` ; do truncate -s 0 file.$i ; "
               "truncate -s 2M file.$i ; done;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Start volume with force to bring all bricks online
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name,
                                              interval_check=10):
            raise Exception("Heal is not yet completed")

        # Check are there any files in split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Check arequal checksum of all the bricks is same
        for subvol in subvols:
            new_arequal = []
            arequal_from_the_bricks = redant.collect_bricks_arequal(subvol)
            for item in arequal_from_the_bricks:
                item = " ".join(item)
                new_arequal.append(item)

            val = len(set(new_arequal))
            if (self.volume_type == "arb" or self.volume_type == "dist-arb"):
                val = len(set(new_arequal[:2]))
            if val != 1:
                raise Exception("Arequal is not same on all the bricks in the"
                                " subvol")
