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

from glusto.core import Glusto as g
from glustolibs.gluster.gluster_base_class import GlusterBaseClass, runs_on
from glustolibs.gluster.exceptions import ExecutionError
from glustolibs.gluster.gluster_init import (
    start_glusterd, stop_glusterd, wait_for_glusterd_to_start)
from glustolibs.gluster.peer_ops import peer_status, wait_for_peers_to_connect
from glustolibs.gluster.volume_ops import volume_list, volume_info
from glustolibs.gluster.volume_libs import (cleanup_volume, setup_volume)
"""


# disruptive;rep

from random import randint
from tests.abstract_test import AbstractTest


class TestOpsWhenOneNodeIsDown(AbstractTest):

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
            redant.wait_for_glusterd_to_start(server)
        redant.logger.info("Glusterd start on the nodes succeeded")

        # Checking if peer is connected.
        redant.wait_for_peers_to_connect(self.server_list[0],
                                         self.server_list)
        redant.logger.info("Peers is in connected state.")
