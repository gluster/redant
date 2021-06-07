"""
Copyright (C) 2019  Red Hat, Inc. <http://www.redhat.com>

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
This test checks the warning message return
on detaching a peer from the cluster.
"""
# disruptive;

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test Case:
        1) Create a cluster.
        2) Peer detach a node and send an 'n'.
        3) Check the warning message.
        4) Check peer status.
           (Node shouldn't be detached!)
        5) Peer detach a node now press y.
        6) Check peer status.
           (Node should be detached!)
        """

        # Peer detach one node
        cmd = f"gluster peer detach {self.server_list[1]}"
        ret = redant.execute_command_async(cmd, self.server_list[0])
        ret['stdin'].write("n\n")
        ret = redant.collect_async_result(ret)
        msg = ret['msg'][0]

        # Checking warning message
        expected_msg = ''.join(['All clients mounted through ',
                                'the peer which is getting detached ',
                                'need to be remounted using one of ',
                                'the other active peers in the ',
                                'trusted storage pool to ensure '
                                'client gets notification ',
                                'on any changes done on the ',
                                'gluster configuration and ',
                                'if the same has been done ',
                                'do you want to proceed'])
        if expected_msg not in msg:
            raise Exception("Incorrect warning message for peer detach.")

        # Checking if peer is connected
        ret = redant.is_peer_connected(self.server_list[1],
                                       self.server_list[0])
        if not ret:
            raise Exception("Peer is not in connected state.")

        # Peer detach one node
        redant.peer_detach(self.server_list[1],
                           self.server_list[0])

        # Checking if peer is connected
        ret = redant.is_peer_connected(self.server_list[1],
                                       self.server_list[0])
        if ret:
            raise Exception("Peer is in connected state.")
