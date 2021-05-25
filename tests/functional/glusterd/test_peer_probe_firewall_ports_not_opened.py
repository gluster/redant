'''
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

 Description: test the peer probe when the firewall service is down
 '''

from random import choice
from tests.d_parent_test import DParentTest

# disruptive;


class TestCase(DParentTest):

    def _remove_firewall_service(self, redant):
        """ Remove glusterfs and rpc-bind services from firewall"""
        for service in ['glusterfs', 'rpc-bind']:
            for option in ("", " --permanent"):
                cmd = (f"firewall-cmd --zone=public --remove-service="
                       f"{service}{option}")
                redant.execute_abstract_op_node(cmd, self.node)
                redant.logger.info("Successfully removed glusterfs and"
                                   "rpc-bind services")

    def _add_firewall_service(self, redant):
        """ Add glusterfs and rpc-bind services from firewall"""
        for service in ['glusterfs', 'rpc-bind']:
            for option in ("", " --permanent"):
                cmd = (f"firewall-cmd --zone=public --add-service="
                       f"{service}{option}")
                redant.execute_abstract_op_node(cmd, self.node)
        redant.logger.info("Successfully removed glusterfs and"
                           "rpc-bind services")

    def run_test(self, redant):
        """
        Test Steps:
        1. Open glusterd port only in  Node1 using firewall-cmd command
        2. Perform peer probe to Node2 from Node 1
        3. Check for core files created
        """
        # Remove firewall service on the node to probe to
        self.node = choice(self.server_list[1:])
        for server in self.server_list[1:]:
            redant.peer_detach(server, self.server_list[0])
        for server in self.server_list:
            cmd = "systemctl restart firewalld"
            redant.execute_abstract_op_node(cmd, server)
        self._remove_firewall_service(redant)

        # Try peer probe from mnode to node
        try:
            redant.peer_probe(self.node, self.server_list[0])
        except:
            msg = (f"Peer probe of {self.node} from"
                   f"{self.server_list[0]} failed as expected ")
            redant.logger.info(msg)

        # Verify no core files are created
        # ret = is_core_file_created(self.servers, test_timestamp)
        # self.assertTrue(ret, "Unexpected crash found.")
        # redant.logger.info("No core file found as expected")

        self._add_firewall_service(redant)
