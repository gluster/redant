"""
  Copyright (C) 2020  Red Hat, Inc. <http://www.redhat.com>

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
    Performs reserve limit change, adds brick and checks
    for reserve limit changes during rebalancing.
"""

import traceback
from tests.d_parent_test import DParentTest


# disruptive;dist-rep
class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = (self.redant.
                   wait_for_rebalance_to_complete(self.vol_name,
                                                  self.server_list[0]))
            if not ret:
                raise Exception("Rebalance not completed. Wait timeout")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1) Create a distributed-replicated volume and start it.
        2) Enable storage.reserve option on the volume using below command,
           gluster volume set storage.reserve 50
        3) Mount the volume on a client
        4) Add some data on the mount point (should be within reserve limits)
        5) Now, add-brick and trigger rebalance.
           While rebalance is in-progress change the reserve limit to a lower
           value say (30)
        6. Stop the rebalance
        7. Reset the storage reserve value to 50 as in step 2
        8. trigger rebalance
        9. while rebalance in-progress change the reserve limit to a higher
           value say (70)
        """

        # Setting storage.reserve 50
        redant.set_volume_options(self.vol_name, {"storage.reserve": "50"},
                                  self.server_list[0])

        # Create a dir to start untar
        self.linux_untar_dir = f"{self.mountpoint}/linux_untar"
        redant.execute_abstract_op_node("mkdir -p "
                                        f"{self.linux_untar_dir}",
                                        self.client_list[0])

        # Start linux untar on dir linux_untar
        redant.run_linux_untar(self.client_list[0], self.mountpoint,
                               dirs=tuple(['linux_untar']))

        # Add bricks to the volume
        mul_factor = 3
        _, br_cmd = redant.form_brick_cmd(self.server_list,
                                          self.brick_roots,
                                          self.vol_name, mul_factor, True)
        redant.add_brick(self.vol_name, br_cmd, self.server_list[0],
                         replica_count=3)

        # Trigger rebalance on the volume
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Setting storage.reserve 30
        redant.set_volume_options(self.vol_name, {"storage.reserve": "30"},
                                  self.server_list[0])

        # Stopping Rebalance
        redant.rebalance_stop(self.vol_name, self.server_list[0])

        # Setting storage.reserve 500
        redant.set_volume_options(self.vol_name, {"storage.reserve": "500"},
                                  self.server_list[0])

        # Trigger rebalance on the volume
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Setting storage.reserve 70
        redant.set_volume_options(self.vol_name, {"storage.reserve": "70"},
                                  self.server_list[0])
