"""
  Copyright (C) 2018  Red Hat, Inc. <http://www.redhat.com>

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
  Checks the probing operation, adding bricks to the probed node
  and checking if the brick is correctly added.
"""

from copy import deepcopy
import socket
from tests.d_parent_test import DParentTest

# disruptive;


class TestPeerStatus(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1) Destroy cluster
        2) Peer Probe 1 server
        3) Get peer status
        4) Create a distributed volume on two node cluster
        5) Peer Probe a third node
        6) Add a brick on third node
        7) Get volume info
        8) Check if the brick is correctly added
        """

        redant.delete_cluster(self.server_list)

        # get FQDN of node1
        node1 = socket.getfqdn(self.server_list[1])

        # peer probe to a new node, N2 from N1
        redant.peer_probe(node1, self.server_list[0])

        # checking if node1 is connected
        ret = redant.wait_for_peers_to_connect(node1,
                                               self.server_list[0])
        if not ret:
            raise Exception("Some peers are not in connected state")

        # check peer status in both the nodes, it should have IP
        # from node1
        ret = redant.get_peer_status(self.server_list[0])
        if ret is None:
            raise Exception("Peer status returned None")
        if self.server_list[1] != socket.gethostbyname(ret['hostname']):
            raise Exception(f"{self.server_list[1]} is not present "
                            "in the output of peer status from "
                            f"{self.server_list[0]}")

        # from node1
        ret = redant.get_peer_status(self.server_list[1])
        if self.server_list[0] != socket.gethostbyname(ret['hostname']):
            raise Exception(f"{self.server_list[0]} is not present "
                            "in the output of peer status from "
                            f"{self.server_list[1]}")

        # create a distributed volume with 2 bricks
        conf_hash = deepcopy(self.vol_type_inf['dist'])
        conf_hash['dist_count'] = 2
        redant.setup_volume(self.vol_name, self.server_list[0],
                            conf_hash, self.server_list[0:2],
                            self.brick_roots, force=True)

        # peer probe to a new node, N3
        redant.peer_probe(self.server_list[2], self.server_list[0])

        # Validate if first three peers are in connected state
        ret = redant.wait_for_peers_to_connect(self.server_list[0:3],
                                               self.server_list[0])
        if not ret:
            raise Exception("Some peers are not in connected state")

        # add a brick from N3 to the volume
        mul_factor = 1
        _, br_cmd = redant.form_brick_cmd([self.server_list[2]],
                                          self.brick_roots, self.vol_name,
                                          mul_factor, True)
        redant.add_brick(self.vol_name, br_cmd, self.server_list[0], True)

        # get volume info, it should have correct brick information
        ret = redant.get_volume_info(self.server_list[0], self.vol_name)
        all_bricks = redant.es.get_all_bricks_list(self.vol_name)
        brick3 = ret[self.vol_name]['bricks'][2]['name']
        if brick3 != str(all_bricks[2]):
            raise Exception("Volume info has incorrect "
                            "information")
