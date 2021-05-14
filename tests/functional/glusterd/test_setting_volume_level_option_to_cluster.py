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

 In this test we are testing the volume level option to cluster
 """

# nonDisruptive;

from tests.abstract_test import AbstractTest


class TestSettingVolumeLevelOptionToCluster(AbstractTest):

    def run_test(self, redant):
        # pylint: disable=too-many-statements
        """
        Test Case:
        1) Create a cluster.
        2) Try to set volume level options to cluster level.
           (These should fail!)
        eg: gluster v set all transport.listen-backlog 128
            gluster v set all performance.parallel-readdir on
        3) Check if glusterd has crashed or not.(Should not crash!)
        """

        # Set transport.listen-backlog to 128 for all volumes.(Should fail!)
        try:
            ret = redant.set_volume_options(
                'all', {'transport.listen-backlog': '128'},
                self.server_list[0])
        except Exception as error:
            redant.logger.info(error)
            redant.logger.info("Successfully tested"
                               " setting transport.listen-backlog"
                               " to 128 for all volumes")

        # Checking if glusterd is running on all the nodes.
        for each_server in self.server_list:
            ret = redant.is_glusterd_running(each_server)

        redant.logger.info("Glusterd is running on all the servers")

        # Checking if all the peers are in connected state or not.
        ret = redant.is_peer_connected(self.server_list[0], self.server_list)
        if not ret:
            raise Exception("All peers are not in connected state.")

        redant.logger.info("All peers are in connected state.")

        # Set performance.parallel-readdir to on for all volumes.(Should fail!)
        try:
            ret = redant.set_volume_options(
                'all', {'performance.parallel-readdir': 'on'},
                self.server_list[0])
        except Exception as error:
            redant.logger.info("EXPECTED: Failed to set parallel-readdir to"
                               " ON for all volumes.")

        # Checking if glusterd is running on all the nodes.
        for each_server in self.server_list:
            ret = redant.is_glusterd_running(each_server)

        redant.logger.info("Glusterd is running on all the servers")

        # Checking if all the peers are in connected state or not.
        ret = redant.is_peer_connected(self.server_list[0], self.server_list)
        if not ret:
            raise Exception("All peers are not in connected state.")

        redant.logger.info("All peers are in connected state.")
