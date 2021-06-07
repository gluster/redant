"""
Copyright (C) 2020-2021 Red Hat, Inc. <http://www.redhat.com>

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
This test deals with probing a peer in which glusterd is down.
"""

# disruptive;

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def _peer_probe_operations(self, hostname):
        # Trying to peer probe the node whose glusterd was stopped using IP
        ret = self.redant.peer_probe(self.server_list[1],
                                     self.server_list[0],
                                     False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Peer probe should have failed"
                            " when glusterd is down.")

        ret = self.redant.peer_probe(hostname,
                                     self.server_list[0],
                                     False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Peer probe should have failed"
                            " when glusterd is down.")

    def run_test(self, redant):
        '''
        Test script to verify the behavior when we try to peer
        probe a valid node whose glusterd is down
        Also post validate to make sure no core files are created
        under "/", /var/log/core and /tmp  directory

        Ref: BZ#1257394 Provide meaningful error on peer probe and peer detach
        Test Steps:
        1 check the current peer status
        2 detach one of the valid nodes which is already part of cluster
        3 stop glusterd on that node
        4 try to attach above node to cluster, which must fail with
          Transport End point error
        5 Recheck the test using hostname, expected to see same result
        6 start glusterd on that node
        7 halt/reboot the node
        8 try to peer probe the halted node, which must fail again.
        9 The only error accepted is
          "peer probe: failed: Probe returned with Transport endpoint is not
          connected"
        10 Check peer status and make sure no other nodes in peer reject state
        '''
        ret = redant.execute_abstract_op_node('date +%s',
                                              self.server_list[0])
        test_timestamp = ret['msg'][0].rstrip('\n').strip()

        # Detach one of the nodes which is part of the cluster
        redant.peer_detach(self.server_list[1],
                           self.server_list[0])

        # Bring down glusterd of the server which has been detached
        redant.stop_glusterd(self.server_list[1])

        if not (redant.
                wait_for_glusterd_to_stop(self.server_list[1])):
            raise Exception(f"Glusterd is still running on"
                            f" {self.server_list[1]}")

        # Trying to peer probe the same node with hostname
        ret = redant.execute_abstract_op_node("hostname",
                                              self.server_list[1])
        hostname = ret['msg'][0].rstrip('\n')

        # perform probing operations
        self._peer_probe_operations(hostname)

        # Start glusterd again for the next set of test steps
        redant.start_glusterd(self.server_list[1])

        if not (redant.
                wait_for_glusterd_to_start(self.server_list[1])):
            raise Exception(f"Glusterd is not running on "
                            f"{self.server_list[1]}")

        # Bring down the network for sometime
        network_status = (redant.
                          bring_down_network_interface(self.server_list[1],
                                                       30))

        # perform probing operations
        self._peer_probe_operations(hostname)

        ret = redant.wait_till_async_command_ends(network_status)
        if ret['error_code'] != 0:
            raise Exception("Failed to perform network interface ops")

        # Peer probe the node must pass
        redant.peer_probe(self.server_list[1], self.server_list[0])

        # Checking if core file created in "/", "/tmp" and "/var/log/core"
        if redant.check_core_file_exists(self.server_list, test_timestamp):
            raise Exception("glusterd service should not have crashed")
