"""
Copyright (C) 2019-2020  Red Hat, Inc. <http://www.redhat.com>

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
This test deals with testing ops when one node is down.
"""


# disruptive;rep

from random import randint
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test Case:
        1) Create a N node gluster cluster.
        2) Stop gluster on one node.
        3) Execute gluster peer status on other node.
        4) Execute gluster v list on other node.
        5) Execute gluster v info on other node.
        6) Start gluster back again
        """

        # Fetching a random server from list.
        random_server = randint(1, len(self.server_list)-1)

        # Stopping glusterd on one node.
        redant.stop_glusterd(self.server_list[random_server])
        redant.logger.info("Successfully stopped glusterd on one node.")

        # Running peer status on another node.
        redant.get_peer_status(self.server_list[0])
        redant.logger.info(f"Successfully got peer status from "
                           f"{self.server_list[0]}.")

        # Running volume list on another node.
        redant.get_volume_list(self.server_list[0])
        redant.logger.info(f"Successfully got volume list from "
                           f"{self.server_list[0]}")

        # Running volume info on another node.
        redant.get_volume_info(self.server_list[0])
        redant.logger.info(f"Successfully got volume info from "
                           f"{self.server_list[0]}")

        # Starting glusterd on node where stopped.
        redant.start_glusterd(self.server_list[random_server])
        redant.logger.info("Successfully started glusterd.")

        for server in self.server_list:
            ret = redant.wait_for_glusterd_to_start(server)
            if not ret:
                raise Exception(f"Failed: Glusterd not started on {server}")
        redant.logger.info("Glusterd start on the nodes succeeded")

        # Checking if peer is connected.
        ret = redant.wait_for_peers_to_connect(self.server_list,
                                               self.server_list[0])
        if not ret:
            raise Exception("Failed : All the peer are not connected")
        redant.logger.info("Peers is in connected state.")
