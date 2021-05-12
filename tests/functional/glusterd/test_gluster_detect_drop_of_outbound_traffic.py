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
      Gluster should detect drop of outbound traffic as network failure
"""

# nonDisruptive;rep,dist,disp,arb,dist-arb,dist-rep

from tests.abstract_test import AbstractTest


class TestGlusterDetectDropOfOutboundTrafficAsNetworkFailure(AbstractTest):

    def run_test(self, redant):
        """
        Test Case:
        1) Create a volume and start it.
        2) Add an iptable rule to drop outbound glusterd traffic
        3) Check if the rule is added in iptables list
        4) Execute few Gluster CLI commands like volume status, peer status
        5) Gluster CLI commands should fail with suitable error message
        """
        server1 = self.server_list[0]

        # Set iptablerule_set as false initially
        iptablerule_set = False

        # Set iptable rule on one node to drop outbound glusterd traffic
        cmd = "iptables -I OUTPUT -p tcp --dport 24007 -j DROP"
        redant.execute_io_cmd(cmd, server1)

        # Update iptablerule_set to true
        iptablerule_set = True

        # Confirm if the iptable rule was added successfully
        iptable_rule = "'OUTPUT -p tcp -m tcp --dport 24007 -j DROP'"
        vol_types = "dist,disp,arb,dist-arb,dist-rep"
        cmd = f"iptables -S OUTPUT | grep,{vol_types} {iptable_rule}"
        redant.execute_io_cmd(cmd, server1)

        # Fetch number of nodes in the pool, except localhost
        pool_list = redant.nodes_from_pool_list(server1)
        peers_count = len(pool_list) - 1

        # Gluster CLI commands should fail
        # Check volume status command
        try:
            redant.get_volume_status(node=server1)
            redant.logger.error("Unexpected: gluster volume status command "
                                "did not return any error")
        except Exception:
            redant.logger.info("Volume status command failed with expected"
                               " error message")

        # Check peer status command and all peers are in 'Disconnected' state
        peer_list = redant.get_peer_status(server1)

        for peer in peer_list:
            if peer["connected"] == 0:
                redant.logger.error("Unexpected: All the peers are not in "
                                    "'Disconnected' state")
            if peer["stateStr"] == "Peer in CLuster":
                redant.logger.error("Peer in Cluster", "Unexpected:All the "
                                    "peers not in 'Peer in Cluster' state")

        if iptablerule_set:
            cmd = "iptables -D OUTPUT -p tcp -m tcp --dport 24007 -j DROP"
            redant.execute_io_cmd(cmd, server1)
