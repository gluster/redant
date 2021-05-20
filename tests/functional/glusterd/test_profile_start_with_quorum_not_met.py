"""
Copyright (C) 2017-2019  Red Hat, Inc. <http://www.redhat.com>

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

This test case deals with starting profile operations when quorum is
not met.
"""

# disruptive;dist,rep,disp,dist-rep,dist-disp

from random import choice
from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Create a volume
        2. Set the quorum type to server and ratio to 90
        3. Stop glusterd randomly on one of the node
        4. Start profile on the volume
        5. Start glusterd on the node where it is stopped
        6. Start profile on the volume
        7. Stop profile on the volume where it is started
        """

        # Enabling server quorum
        quorum_options = {'cluster.server-quorum-type': 'server'}
        redant.set_volume_options(self.vol_name, quorum_options,
                                  self.server_list[0])

        # Setting Quorum ratio to 90%
        quorum_perecent = {'cluster.server-quorum-ratio': '90%'}
        redant.set_volume_options('all', quorum_perecent,
                                  self.server_list[0])

        # Stop glusterd on one of the node randomly
        node_on_glusterd_to_stop = choice(self.server_list[1:])
        redant.stop_glusterd(node_on_glusterd_to_stop)

        # checking whether peers are connected or not
        for _ in range(5):
            ret = redant.validate_peers_are_connected(self.server_list[:],
                                                      self.server_list[0])
            if ret:
                break
            sleep(2)

        if ret:
            redant.logger.error("Peers are in connected state even after "
                                "stopping glusterd on one node")

        # Starting volume profile when quorum is not met
        new_servers = self.server_list[:]
        new_servers.remove(node_on_glusterd_to_stop)

        try:
            redant.profile_start(self.vol_name, choice(new_servers))

        except Exception:
            redant.logger.info("Profile start failed as expected")

        # Start glusterd on the node where it is stopped
        redant.start_glusterd(node_on_glusterd_to_stop)

        for _ in range(5):
            ret = redant.validate_peers_are_connected(self.server_list[:],
                                                      self.server_list[0])
            if not ret:
                break
            sleep(2)

        if not ret:
            redant.logger.error("Peers are not in connected state")

        # Starting profile when volume quorum is met
        redant.profile_start(self.vol_name, self.server_list[0])

        # Stop the profile
        redant.profile_stop(self.vol_name, self.server_list[0])
