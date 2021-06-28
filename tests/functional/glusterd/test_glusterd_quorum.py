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
    TC to check glusterd quorum
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;rep,dist-rep


class TestCase(DParentTest):

    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.setup_done = True

    def terminate(self):
        """
        Cleanup the volume created in the TC
        """
        try:
            # Start glusterd on all servers
            self.redant.start_glusterd(self.server_list)
            if not self.redant.wait_for_glusterd_to_start(self.server_list):
                raise Exception("Failed to start glusterd on all nodes")

            if self.vol_exist:
                self.redant.cleanup_volume(self.volume_name1,
                                           self.server_list[0])

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        -> Creating two volumes and starting them, stop the second volume
        -> set the server quorum and set the ratio to 90
        -> Stop the glusterd in one of the node, so the quorum won't meet
        -> Peer probing a new node should fail
        -> Volume stop will fail
        -> volume delete will fail
        -> volume reset will fail
        -> Start the glusterd on the node where it is stopped
        -> Volume stop, start, delete will succeed once quorum is met
        """
        self.vol_exist = False

        # Exit if cluster size less than 4
        if len(self.server_list) < 4:
            self.TEST_RES = None
            raise Exception("Minimum 4 nodes required for this TC to run")

        # Peer probe first 3 servers
        redant.create_cluster(self.server_list[:3])
        redant.wait_for_peers_to_connect(self.server_list[:3],
                                         self.server_list[0])

        # Create a volume using the first 3 nodes
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type]]
        redant.setup_volume(self.vol_name, self.server_list[0],
                            conf_dict, self.server_list[:3],
                            self.brick_roots)

        # Creating another volume and stopping it
        self.volume_type1 = 'dist'
        self.volume_name1 = f"{self.test_name}-1"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
        redant.setup_volume(self.volume_name1, self.server_list[0],
                            conf_dict, self.server_list[:3],
                            self.brick_roots)
        self.vol_exist = True

        # stopping the second volume
        redant.volume_stop(self.volume_name1, self.server_list[0])

        # Setting the server-quorum-type as server
        self.options = {"cluster.server-quorum-type": "server"}
        vol_list = redant.get_volume_list(self.server_list[0])
        if vol_list is None:
            raise Exception("Failed to get the volume list")

        for volume in vol_list:
            redant.set_volume_options(volume, self.options,
                                      self.server_list[0])

        # Setting the server quorum ratio to 90
        self.quorum_perecent = {'cluster.server-quorum-ratio': '90%'}
        redant.set_volume_options('all', self.quorum_perecent,
                                  self.server_list[0])

        # Stop glusterd on one of the node
        redant.stop_glusterd(self.server_list[2])

        # Check glusterd is stopped
        if not redant.wait_for_glusterd_to_stop(self.server_list[2]):
            raise Exception("Unexpected: Glusterd is running on node")

        # Adding a new peer will fail as quorum not met
        ret = redant.peer_probe(self.server_list[3], self.server_list[0],
                                False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Unexpected: Succeeded to peer probe new node"
                            f" {self.server_list[3]} when quorum is not met")

        # Stopping an already started volume should fail as quorum is not met
        ret = redant.volume_start(self.volume_name1, self.server_list[0],
                                  False, False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Unexpected: Successfuly started "
                            "volume even when quorum not met.")

        # Stopping a volume should fail stop the first volume
        ret = redant.volume_stop(self.vol_name, self.server_list[0], False,
                                 False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Unexpected: Successfully stopped"
                            " volume even when quourm is not met")

        # Stopping a volume with force option should fail
        ret = redant.volume_stop(self.vol_name, self.server_list[0], True,
                                 False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Unexpected: Successfully "
                            "stopped volume with force. Expected: "
                            "Volume stop should fail when quourm is not met")

        # Deleting a volume should fail. Deleting the second volume.
        ret = redant.volume_delete(self.volume_name1, self.server_list[0],
                                   False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Volume delete was "
                            "successful even when quourm is not met")

        # Volume reset should fail when quorum is not met
        ret = redant.volume_reset(self.vol_name, self.server_list[0], False,
                                  False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Unexpected: Volume reset was "
                            "successful even when quorum is not met")

        # Volume reset should fail even with force when quourum is not met
        ret = redant.volume_reset(self.vol_name, self.server_list[0], True,
                                  False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Unexpected: Volume reset was "
                            "successful with force even when quorum is"
                            " not met")

        # Start glusterd on the node where glusterd is stopped
        redant.start_glusterd(self.server_list[2])

        if not redant.wait_for_glusterd_to_start(self.server_list[2]):
            raise Exception("glusterd is not running on "
                            f"node: {self.server_list[2]}")

        # Check peer status whether all peer are in connected state none of the
        # nodes should be in peer rejected state
        if not redant.wait_till_all_peers_connected(self.server_list[:3], 30):
            raise Exception("Peers are not connected state after "
                            "bringing back glusterd online on the "
                            "nodes in which previously glusterd "
                            "had been stopped")

        # Check all bricks are online or wait for the bricks to be online
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get the brick list")
        if not redant.wait_for_bricks_to_come_online(self.vol_name,
                                                     self.server_list,
                                                     brick_list):
            raise Exception("All bricks are not online")

        # Once quorum is met should be able to cleanup the volume
        redant.volume_delete(self.volume_name1, self.server_list[0])
        self.vol_exist = False

        # Volume stop should succeed
        redant.volume_stop(self.vol_name, self.server_list[0])

        # volume reset should succeed
        redant.volume_reset(self.vol_name, self.server_list[0])

        # Peer probe new node should succeed
        redant.peer_probe(self.server_list[3], self.server_list[0])

        # Check peer status whether all peer are in connected state none of the
        # nodes should be in peer rejected state
        if not redant.wait_till_all_peers_connected(self.server_list[:3], 30):
            raise Exception("Peers are not connected state after "
                            "bringing back glusterd online on the "
                            "nodes in which previously glusterd "
                            "had been stopped")
