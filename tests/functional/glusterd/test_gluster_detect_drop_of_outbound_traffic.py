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

import traceback
from tests.d_parent_test import DParentTest

# disruptive;rep,dist,disp,arb,dist-arb,dist-rep


class TestGlusterDetectDropOfOutboundTrafficAsNetworkFailure(DParentTest):

    def terminate(self):
        """
        Update the iptables to remove the DROP rule
        """
        try:
            if self.iptablerule_set:
                cmd = "iptables -D OUTPUT -p tcp -m tcp --dport 24007 -j DROP"
                self.redant.execute_abstract_op_node(cmd, self.server1)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test Case:
        1) Create a volume and start it.
        2) Add an iptable rule to drop outbound glusterd traffic
        3) Check if the rule is added in iptables list
        4) Execute few Gluster CLI commands like volume status, peer status
        5) Gluster CLI commands should fail with suitable error message
        """
        self.server1 = self.server_list[1]

        # Set iptablerule_set as false initially
        self.iptablerule_set = False

        # Set iptable rule on one node to drop outbound glusterd traffic
        cmd = "iptables -I OUTPUT -p tcp --dport 24007 -j DROP"
        redant.execute_abstract_op_node(cmd, self.server1)

        # Update iptablerule_set to true
        self.iptablerule_set = True

        # Confirm if the iptable rule was added successfully
        iptable_rule = "'OUTPUT -p tcp -m tcp --dport 24007 -j DROP'"
        cmd = f"iptables -S OUTPUT | grep {iptable_rule} | wc -l"
        ret = redant.execute_abstract_op_node(cmd, self.server1, False)
        if ret['error_code'] != 0:
            raise Exception("Failed to get the iptables rule output")

        if int(ret['msg'][0].rstrip('\n')) != 1:
            raise Exception("Failed to find the rule in the iptables"
                            "rule list")

        # Fetch number of nodes in the pool, except localhost
        pool_list = redant.nodes_from_pool_list(self.server1)
        peers_count = len(pool_list) - 1

        # Gluster CLI commands should fail
        # Check volume status command
        vol_status = redant.get_volume_status(self.vol_name, self.server1,
                                              excep=False)
        if vol_status['msg']['opRet'] == '0':
            raise Exception("Successfully got the volume status")

        err_str = vol_status['msg']['opErrstr']
        err_count_staging = err_str.count("Staging failed on")
        err_count_locking = err_str.count("Locking failed on")
        if peers_count not in (err_count_staging, err_count_locking):
            raise Exception("Unexpected: Number of nodes on which command"
                            " failed is not equal to the peers count")

        # Check peer status command and all peers are in 'Disconnected' state
        peer_list = redant.get_peer_status(self.server1)

        for peer in peer_list:
            if peer["connected"] != '0':
                raise Exception("Unexpected: All the peers are not in "
                                "'Disconnected' state")
            if peer["stateStr"] != 'Peer in Cluster':
                raise Exception("Unexpected:All the peers not in"
                                " 'Peer in Cluster' state")
