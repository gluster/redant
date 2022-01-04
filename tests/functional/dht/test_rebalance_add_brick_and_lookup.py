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
    Rebalance with add brick and log time taken for lookup
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
from time import time
from tests.d_parent_test import DParentTest


class TestRebalanceWithAddBrickAndLookup(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Run TC only on RHGS installation
        self.redant.check_rhgs_installation(self.server_list)

        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def run_test(self, redant):
        """
        Steps:
        - Create a Distributed-Replicated volume.
        - Create deep dirs(200) and 100 files on the deepest directory.
        - Expand volume.
        - Initiate rebalance
        - Once rebalance is completed, do a lookup on mount and time it.
        """
        # Create Deep dirs.
        cmd = (f"cd {self.mountpoint}/; for i in {{1..200}};do mkdir "
               "dir${i}; cd dir${i}; if [ ${i} -eq 100 ]; then for j in"
               " {1..100}; do touch file${j}; done; fi; done;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Expand the volume.
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to expand the volume {self.vol_name}")

        # Start Rebalance.
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=500)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Do a lookup on the mountpoint and note the time taken to run.
        # The time used for comparison is taken as a benchmark on using a
        # RHGS 3.5.2 for this TC. For 3.5.2, the time takes came out to be
        # 4 seconds. Now the condition for subtest to pass is for the lookup
        # should not be more than 10% of this value, i.e. 4.4 seconds.
        cmd = f"ls -R {self.mountpoint}/"
        start_time = time()
        redant.execute_abstract_op_node(cmd, self.client_list[0])
        end_time = time()
        time_taken = end_time - start_time
        redant.logger.info(f"Lookup took : {time_taken} seconds")
