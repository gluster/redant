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
    Test verifies self-heal on replicated volume types after add-brick.
"""

# disruptive;rep,arb,dist-rep,dist-arb

from time import sleep
from random import sample
import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails early
        """
        try:
            if not self.io_validation_complete:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mnt_list)):
                    raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test Steps:
        1. Create a replicated/distributed-replicate volume and mount it
        2. Start IO from the clients
        3. Bring down a brick from the subvol and validate it is offline
        4. Bring back the brick online and wait for heal to complete
        5. Once the heal is completed, expand the volume.
        6. Trigger rebalance and wait for rebalance to complete
        7. Validate IO, no errors during the steps performed from step 2
        8. Check arequal of the subvol and all the brick in the same subvol
        should have same checksum
        """
        self.io_validation_complete = True

        # Get mount point list
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Start IO from the clients
        self.all_mounts_procs = []
        for count, mount_obj in enumerate(self.mnt_list):
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 1, 2, 2, 30,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            self.io_validation_complete = False

        # Get Subvols
        subvols_list = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols_list:
            redant.logger.error("No Sub-Volumes available for the volume "
                                f"{self.vol_name}")
            return None

        # List a brick in each subvol and bring them offline
        brick_to_bring_offline = []
        for subvol in subvols_list:
            brick_to_bring_offline.extend(sample(subvol, 1))

        redant.bring_bricks_offline(self.vol_name,
                                    brick_to_bring_offline)

        # Validate the brick is offline
        if not redant.are_bricks_offline(self.vol_name, brick_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Bricks {brick_to_bring_offline} are not offline")

        # Wait for 10 seconds for IO to be generated
        sleep(10)

        # Start volume with force to bring all bricks online
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Verifying all bricks online
        if not (redant.verify_all_process_of_volume_are_online(
                self.vol_name, self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # Check are there any files in split-brain and heal completion
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Expanding volume by adding bricks to the volume when IO in progress
        if not (redant.expand_volume(self.server_list[0], self.vol_name,
                                     self.server_list, self.brick_roots)):
            raise Exception("Failed to expand volume")

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Without sleep the next step will fail with Glusterd Syncop locking.
        sleep(2)

        # Wait for rebalance to complete
        if not (redant.wait_for_rebalance_to_complete(self.vol_name,
                                                      self.server_list[0])):
            raise Exception("Rebalance operation has not yet completed.")

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs, self.mnt_list):
            raise Exception("IO operations failed on some"
                            " or all of the clients")

        self.io_validation_complete = True

        # List all files and dirs created
        if not (redant.list_all_files_and_dirs_mounts(self.mnt_list)):
            raise Exception("Failed to list files and dirs")

        # Check arequal checksum of all the bricks is same
        for subvol in subvols_list:
            new_arequal = []
            arequals = redant.collect_bricks_arequal(subvol)
            for item in arequals:
                item = " ".join(item)
                new_arequal.append(item)

            val = len(set(new_arequal))
            if (self.volume_type == "arb" or self.volume_type == "dist-arb"):
                val = len(set(new_arequal[:2]))
            if val != 1:
                raise Exception("Mismatch of arequal checksum")
