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
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    TC to test rebalance while peer probe
"""

# disruptive;dist
from copy import deepcopy
from time import sleep
import traceback
from tests.d_parent_test import DParentTest


class TestRebalancePeerProbe(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Check server requirements
        self.redant.check_hardware_requirements(servers=self.server_list,
                                                servers_count=4)
        self.srvr_cnt = len(self.server_list)

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash,
                                 self.server_list[:self.srvr_cnt - 1],
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def terminate(self):
        """
        Peer probe the detached server, if the TC fails
        """
        try:
            if self.is_peer_detached:
                if not (self.redant.peer_probe_servers(
                        self.server_list[self.srvr_cnt - 1],
                        self.server_list[0])):
                    raise Exception("Failed to peer probe server "
                                    f"{self.server_list[self.srvr_cnt - 1]}")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Detach a peer
        2. Create a volume, start it and mount it
        3. Start creating a few files on mount point
        4. Collect arequal checksum on mount point pre-rebalance
        5. Expand the volume
        6. Start rebalance
        7. While rebalance is going, probe a peer and check if
           the peer was probed successfully
        7. Collect arequal checksum on mount point post-rebalance
           and compare wth value from step 4
        """
        self.is_peer_detached = False

        # Detach a peer
        redant.peer_detach(self.server_list[self.srvr_cnt - 1],
                           self.server_list[0])
        self.is_peer_detached = True

        # Start I/O from mount point and wait for it to complete
        cmd = (f"cd {self.mountpoint}; for i in {{1..1000}} ; do "
               "dd if=/dev/urandom of=file$i bs=10M count=1; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Collect arequal checksum before rebalance
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts)

        # Add brick to volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list[:self.srvr_cnt - 1],
                                   self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Trigger rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0], force=True)

        # Let rebalance run for a while
        sleep(5)

        # Add new node to the cluster
        ret = redant.peer_probe_servers(self.server_list[self.srvr_cnt - 1],
                                        self.server_list[0])
        if not ret:
            raise Exception("Failed to peer probe server "
                            f"{self.server_list[self.srvr_cnt - 1]}")

        self.is_peer_detached = False

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=1200)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Collect arequal checksum after rebalance
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts)

        # Check for data loss by comparing arequal before and after rebalance
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum is NOT MATCHNG")
