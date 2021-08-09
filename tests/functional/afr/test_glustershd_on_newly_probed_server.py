"""
 Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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
    TC to verify glustershd process on newly probed server
"""

# disruptive;rep,dist-rep
# TODO: NFS, CIFS
from tests.d_parent_test import DParentTest


class TestSelfHealDaemonProcessTests(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the cluster formation, volume create and start in
        parent_run_test
        """
        if len(self.server_list) < 6:
            self.TEST_RES = None
            raise Exception("The test case require 6 servers to run the test")

        self.extra_servers = self.server_list[-2:]
        self.servers = self.server_list[:-2]
        if not self.redant.peer_detach_servers(self.extra_servers,
                                               self.server_list[0]):
            raise Exception("Peer detach failed")

        self.redant.setup_volume(self.vol_name, self.servers[0],
                                 self.vol_type_inf[self.volume_type],
                                 self.servers, self.brick_roots)

        # Verfiy glustershd process releases its parent process
        if not self.redant.is_shd_daemonized(self.servers):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

    def run_test(self, redant):
        """
        * check glustershd process - only 1 glustershd process should
          be running
        * Add new node to cluster
        * check glustershd process - only 1 glustershd process should
          be running on all servers inclusing newly probed server
        * stop the volume
        * add another node to cluster
        * check glustershd process - glustershd process shouldn't be running
          on servers including newly probed server
        * start the volume
        * check glustershd process - only 1 glustershd process should
          be running on all servers inclusing newly probed server

        """
        nodes = self.servers[:]

        # check the self-heal daemon process
        ret, pids = redant.get_self_heal_daemon_pid(nodes)
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process "
                            f"found : {pids}")

        # Add new node to the cluster
        if not redant.peer_probe_servers(self.extra_servers[0],
                                         self.servers[0]):
            raise Exception("Failed to peer probe server "
                            f"{self.extra_servers[0]}")
        nodes.append(self.extra_servers[0])

        # check the self-heal daemon process and it should be running on
        # newly probed servers
        ret, pids = redant.get_self_heal_daemon_pid(nodes)
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than one self heal daemon process "
                            f"found : {pids}")

        # stop the volume
        redant.volume_stop(self.vol_name, self.servers[0])

        # Add another new node to the cluster
        if not redant.peer_probe_servers(self.extra_servers[1],
                                         self.servers[0]):
            raise Exception("Failed to peer probe server "
                            f"{self.extra_servers[1]}")
        nodes.append(self.extra_servers[1])

        # check the self-heal daemon process after stopping volume and
        # no self heal daemon should be running including newly probed node
        ret, pids = redant.get_self_heal_daemon_pid(nodes)
        if ret:
            raise Exception("Self Heal Daemon process is running even "
                            f"after stopping volume {self.volname}")

        for node in pids:
            if pids[node] != -1:
                raise Exception("Self Heal Daemon is still running on node"
                                f" {node} even after stopping all volumes")

        # start the volume
        redant.volume_start(self.vol_name, self.servers[0])

        # Verify volume's all process are online for 60 sec
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.servers[0], nodes, 60)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verfiy glustershd process releases its parent process
        if not redant.is_shd_daemonized(nodes):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # check the self-heal daemon process
        ret, pids = redant.get_self_heal_daemon_pid(nodes)
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than one self heal daemon process "
                            f"found : {pids}")

        # detach extra servers from the cluster
        if not self.redant.peer_detach_servers(self.extra_servers,
                                               self.servers[0]):
            raise Exception("Peer detach failed")
