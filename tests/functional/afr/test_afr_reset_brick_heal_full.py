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
    TC to check heal full after reset brick
"""

# disruptive;rep,dist-rep
# TODO: NFS

import traceback
from random import choice
from tests.d_parent_test import DParentTest


class TestAfrResetBrickHeal(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails midway
        """
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
         1. Create files/dirs from mount point
         2. With IO in progress execute reset-brick start
         3. Now format the disk from back-end, using rm -rf <brick path>
         4. Execute reset brick commit and check for the brick is online.
         5. Issue volume heal using "gluster vol heal <volname> full"
         6. Check arequal for all bricks to verify all backend bricks
            including the resetted brick have same data
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for count, mount_obj in enumerate(self.mounts):
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 3, 5, 5, 5,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)

        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if all_bricks is None:
            raise Exception("Unable to fetch bricks of volume")
        brick_to_reset = choice(all_bricks)

        # Start reset brick
        redant.reset_brick(self.server_list[0], self.vol_name, brick_to_reset,
                           "start")

        # Validate the brick is offline
        if not redant.are_bricks_offline(self.vol_name, brick_to_reset,
                                         self.server_list[0]):
            raise Exception(f"Brick:{brick_to_reset} is still online")

        # rm -rf of the brick directory
        node, brick_path = brick_to_reset.split(":")
        if not redant.rmdir(brick_path, node, force=True):
            raise Exception("Unable to delete the brick "
                            f"{brick_to_reset} on node {node}")

        # Reset brick commit
        redant.reset_brick(self.server_list[0], self.vol_name, brick_to_reset,
                           "commit")

        # Check the brick is online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.vol_name}")

        # Trigger full heal
        if not redant.trigger_heal_full(self.vol_name, self.server_list[0]):
            raise Exception("Unabel to trigger heal full")

        # Wait for the heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # Validate io on the clients
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed on the mounts")

        # Check arequal of the back-end bricks after heal completion
        all_subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        for subvol in all_subvols:
            new_arequal = []
            arequal_from_subvol = redant.collect_bricks_arequal(subvol)
            for item in arequal_from_subvol:
                item = " ".join(item)
                new_arequal.append(item)

            if len(set(new_arequal)) != 1:
                raise Exception("Arequal is not same on all the bricks in "
                                "the subvol")
