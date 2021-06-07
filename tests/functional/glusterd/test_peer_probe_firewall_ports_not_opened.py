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
   TC to check peer probe with firewall ports not opened
"""

import traceback
from random import choice
from tests.d_parent_test import DParentTest

# disruptive;


class TestPeerProbeWithFirewallNotOpened(DParentTest):

    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.setup_done = True
        self.redant.delete_cluster(self.server_list)

    def terminate(self):
        """
        Restore the firewall services in the node
        """
        try:
            # Add the removed services in firewall
            for service in ('glusterfs', 'rpc-bind'):
                for option in ("", " --permanent"):
                    cmd = ("firewall-cmd --zone=public --add-service="
                           f"{service} {option}")
                    self.redant.execute_abstract_op_node(cmd,
                                                         self.node_to_probe)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _remove_firewall_service(self):
        """ Remove glusterfs and rpc-bind services from firewall"""
        for service in ['glusterfs', 'rpc-bind']:
            for option in ("", " --permanent"):
                cmd = ("firewall-cmd --zone=public --remove-service="
                       f"{service} {option}")
                self.redant.execute_abstract_op_node(cmd, self.node_to_probe)

    def run_test(self, redant):
        """
        Test Steps:
        1. Open glusterd port only in  Node1 using firewall-cmd command
        2. Perform peer probe to Node2 from Node 1
        3. Verify glusterd.log for Errors
        4. Check for core files created
        """
        # Timestamp of current test case of start time
        ret = redant.execute_abstract_op_node('date +%s', self.server_list[0])
        test_timestamp = ret['msg'][0].rstrip('\n')

        # Add a log in the glusterd log file, to compare later
        cmd = ("echo 'peer_probe_firewall_test_start' >> "
               "/var/log/glusterfs/glusterd.log")
        redant.execute_abstract_op_node(cmd, self.server_list[0])

        # Remove firewall service on the node to probe to
        self.node_to_probe = choice(self.server_list[1:])
        self._remove_firewall_service()

        # Try peer probe from mnode to node
        ret = redant.peer_probe(self.node_to_probe, self.server_list[0],
                                False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Peer probing the node should have failed")

        expected_err = ('Probe returned with Transport endpoint is not'
                        'connected')
        if expected_err != ret['msg']['opErrstr']:
            raise Exception("Peer probe failed due to unexpected error")

        # Verify there are no glusterd crashes
        cmd = ("awk '/peer_probe_firewall_test_start/,0'"
               " /var/log/glusterfs/glusterd.log | grep ' E ' | wc -l")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        if ret['msg'][0].rstrip('\n') != '0':
            raise Exception("Error logs found in glusterd log file")

        # Verify no core files are created
        # Checking for core files.
        ret = redant.check_core_file_exists(self.server_list, test_timestamp)
        if ret:
            raise Exception("glusterd service should not have crashed")
