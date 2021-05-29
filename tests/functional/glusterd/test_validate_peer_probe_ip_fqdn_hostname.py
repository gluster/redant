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
"""

from socket import gethostbyname, getfqdn
from random import choice
from tests.d_parent_test import DParentTest


# disruptive;
class TestPeerProbeScenarios(DParentTest):

    def _get_node_identifiers(self, redant):
        """
        Returns node address dict with ip, fqdn, hostname as keys
        """
        node = {}
        node['ip'] = gethostbyname(self.node)
        node['fqdn'] = getfqdn(self.node)

        ret = redant.execute_abstract_op_node("hostname", self.node)
        hostname = " ".join(ret['msg']).rstrip("\n")

        node["hostname"] = hostname

        return node

    def _get_new_nodes_to_peer_probe(self, redant):
        """
        Selects a node randomly from the existing set of nodes
        """
        self.node = choice(self.server_list[1:])
        redant.peer_detach(self.node, self.server_list[0])

        return self._get_node_identifiers(redant)

    def _verify_cmd_history(self, redant, node):
        """
        Verifies cmd_history for successful entry of peer probe of nodes
        """

        # Extract the test specific cmds from cmd_history
        cmd_history_log = "/var/log/glusterfs/cmd_history.log"
        cmd = (f"cat {cmd_history_log}")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])

        # Verify the cmd is found from the extracted cmd log
        peer_probe_cmd = f"peer probe {node} : SUCCESS\n"
        test_specific_cmd_history = " ".join(ret['msg'])

        if test_specific_cmd_history.count(peer_probe_cmd) != 0:
            raise Exception("Peer probe success entry not found"
                            " in cmd history")

    def run_test(self, redant):
        """
        1. Clean the cmd_history.log file to verify peer probe success
           for the peer being probed for that particular iteration
        2. Add one of the node(HOST1-IP) to the other node(HOST2-IP) and
           form the cluster
           # gluster peer probe <HOST-IP>
        3. Check the return value of the 'peer probe' command
        4. Confirm that the cluster is formed successfully by 'peer status'
           command
           # gluster peer status
        5. Execute 'pool list' command to get the status of the cluster
           including the local node itself
           # gluster pool list
        6. Check the cmd_history' for the status message related to
          'peer probe' command
        7. Repeat 1-5 for FQDN and hostnames
        """
        self.by_type = ""
        self.node = None

        for self.by_type in ('ip', 'fqdn', 'hostname'):
            # clearing out cmd history from /var/log/glusterfs/cmd_history.log
            cmd = "> /var/log/glusterfs/cmd_history.log"
            redant.execute_abstract_op_node(cmd, self.server_list[0])

            # Get a node to peer probe to
            host_node = self._get_new_nodes_to_peer_probe(redant)

            # Perform peer probe and verify the status
            redant.peer_probe(host_node[self.by_type], self.server_list[0])

            # Verify Peer pool list and check whether the node exists or not
            redant.is_peer_connected(self.server_list[0], host_node['ip'])

            # Verify command history for successful peer probe status
            self._verify_cmd_history(redant, host_node[self.by_type])
