"""
Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check volume set when quorum is enabled
"""

import traceback
from random import choice
from time import sleep
from tests.d_parent_test import DParentTest


# disruptive;dist,rep,disp,dist-rep,dist-disp

class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway and one of the nodes has
        glusterd stopped then the glusterd is started on that node
        and then the terminate function in the DParentTest is called
        """
        try:
            self.redant.start_glusterd(self.node_on_glusterd_to_stop)
            node = self.node_on_glusterd_to_stop
            self.redant.wait_for_glusterd_to_start(node)
        except Exception as error:
            tb = traceback.format_exec()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Create a volume
        Set the quorum type to server and ratio to 90
        Stop glusterd randomly on one of the node
        Set the volume option on the volume
        Start glusterd on the node where it is stopped
        Set the volume option on the volume
        """
        # set cluster.server-quorum-type as server
        redant.set_volume_options(self.vol_name,
                                  {'cluster.server-quorum-type': 'server'},
                                  self.server_list[0])

        # Setting quorum ratio to 90%
        redant.set_volume_options('all',
                                  {'cluster.server-quorum-ratio': '90%'},
                                  self.server_list[0])

        # Stop glusterd on one of the node randomly
        self.node_on_glusterd_to_stop = choice(self.server_list[1:])
        redant.stop_glusterd(self.node_on_glusterd_to_stop)

        # checking whether peers are connected or not
        count = 0
        while count < 5:
            sleep(2)
            ret = redant.validate_peers_are_connected(self.server_list,
                                                      self.server_list[0])
            if not ret:
                break
            count += 1

        if ret:
            raise Exception("Peers are still in connected state")

        # Setting volume option when quorum is not met
        self.new_servers = self.server_list[1:]
        self.new_servers.remove(self.node_on_glusterd_to_stop)
        self.nfs_options = {"nfs.disable": "off"}
        try:
            redant.set_volume_options(self.vol_name,
                                      self.nfs_options,
                                      choice(self.new_servers), False)
        except Exception as error:
            redant.logger.info(f"Volume set failed as expected : {error}")

        # Start glusterd on the node where it is stopped
        redant.start_glusterd(self.node_on_glusterd_to_stop)

        # checking whether peers are connected or not
        count = 0
        while count < 5:
            sleep(2)
            ret = redant.validate_peers_are_connected(self.server_list,
                                                      self.server_list[0])
            if ret:
                break
            count += 1

        # Setting the volume option when quorum is met
        redant.set_volume_options(self.vol_name,
                                  self.nfs_options,
                                  self.server_list[0])
