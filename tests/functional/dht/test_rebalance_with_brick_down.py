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
  51 Franklin Street, Fifth Floor, Boston, MA 02110-131 USA.

Description:
    Rebalance with one brick down in replica
"""
# disruptive;dist-arb,dist-rep,dist-disp

from random import choice
from tests.d_parent_test import DParentTest


class TestRebalanceWithBrickDown(DParentTest):
    """ Rebalance with brick down in replica"""

    def run_test(self, redant):
        """
        Rebalance with brick down in replica
        - Create a Replica volume.
        - Bring down one of the brick down in the replica pair
        - Do some IO and create files on the mount point
        - Add a pair of bricks to the volume
        - Initiate rebalance
        - Bring back the brick which was down.
        - After self heal happens, all the files should be present.
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Log the volume info and status before brick is down.
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Bring one fo the bricks offline
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        ret = redant.bring_bricks_offline(self.vol_name, choice(brick_list))
        if not ret:
            raise Exception("Error in bringing down brick")

        # Log the volume info and status after brick is down.
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Create files at mountpoint.
        proc = redant.create_files(num_files=2000,
                                   fix_fil_size="1k",
                                   path=self.mountpoint,
                                   node=self.client_list[0])

        # Wait for IO to complete.
        ret = redant.wait_for_io_to_complete(proc, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Compute the arequal checksum before bringing all bricks online
        before_all_bricks_online = redant.collect_mounts_arequal(self.mounts)

        # Log the volume info and status before expanding volume.
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Expand the volume.
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=True)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Log the voluem info after expanding volume.
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Start Rebalance.
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=600)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Log the voluem info and status before bringing all bricks online
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Bring all bricks online.
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Log the volume info and status after bringing all beicks online
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Monitor heal completion.
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # Compute the arequal checksum after all bricks online.
        after_all_bricks_online = redant.collect_mounts_arequal(self.mounts)

        # Comparing arequal checksum before and after the operations.
        if before_all_bricks_online != after_all_bricks_online:
            raise Exception("arequal checksum is NOT MATCHNG")
