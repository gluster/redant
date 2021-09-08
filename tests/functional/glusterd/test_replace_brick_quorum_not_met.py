"""
 Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test replace brick when quorum not met
"""

from copy import deepcopy
import random
from tests.d_parent_test import DParentTest

# disruptive;dist-rep


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """

    def run_test(self, redant):
        '''
        -> Create volume
        -> Set quorum type
        -> Set quorum ratio to 95%
        -> Start the volume
        -> Stop the glusterd on one node
        -> Now quorum is in not met condition
        -> Check all bricks went to offline or not
        -> Perform replace brick operation
        -> Start glusterd on same node which is already stopped
        -> Check all bricks are in online or not
        -> Verify in vol info that old brick not replaced with new brick
        '''

        # Create Volume
        self.volume_type = "dist-rep"
        self.vol_name = (f"{self.test_name}-{self.volume_type}")
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        redant.volume_create(self.vol_name, self.server_list[0], conf_hash,
                             self.server_list, self.brick_roots)

        # Get brick list for the volume
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get the brick list")

        # Enabling server quorum
        redant.set_volume_options(self.vol_name,
                                  {'cluster.server-quorum-type': 'server'},
                                  self.server_list[0])

        # Setting Quorum ratio in percentage
        redant.set_volume_options('all',
                                  {'cluster.server-quorum-ratio': '95%'},
                                  self.server_list[0])

        # Start the volume
        redant.volume_start(self.vol_name, self.server_list[0])

        # Stop glusterd on one of the node
        random_server = random.choice(self.server_list[1:])
        redant.stop_glusterd(random_server)

        # Checking whether glusterd is running or not
        if not redant.wait_for_glusterd_to_stop(random_server):
            raise Exception("Glusterd is till running on node: "
                            f"{random_server}")

        # creating brick list from volume status
        vol_status = redant.get_volume_status(self.vol_name,
                                              self.server_list[0])
        if vol_status is None:
            raise Exception("Failed to get volume status")

        offline_bricks = []
        for node in vol_status[self.vol_name]['node']:
            if node['hostname'] != 'Self-heal Daemon':
                offline_bricks.append(':'.join([node['hostname'],
                                      node['path']]))

        # Checking bricks are offline or not with quorum ratio(95%)
        if not redant.are_bricks_offline(self.vol_name, offline_bricks,
                                         self.server_list[0]):
            raise Exception("Bricks are not offline when quorum is not met")

        # Getting random brick from offline brick list
        self.random_brick = random.choice(offline_bricks)

        # Performing replace brick commit force when quorum not met
        self.replace_brick_failed = False
        _, self.new_brick = redant.form_brick_cmd(self.server_list,
                                                  self.brick_roots,
                                                  self.vol_name,
                                                  1, True)
        ret = redant.replace_brick(self.server_list[0], self.vol_name,
                                   self.random_brick, self.new_brick, False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Replace brick should have failed when quorum is"
                            " not met")
        self.replace_brick_failed = True

        # Start glusterd on one of the node
        redant.start_glusterd(random_server)

        if not redant.wait_for_glusterd_to_start(random_server):
            raise Exception("Glusterd is till running on node: "
                            f"{random_server}")

        # Checking bricks are online or not
        new_brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
        if new_brick_list is None:
            raise Exception("Failed to get the brick list")

        if not redant.wait_for_bricks_to_come_online(self.vol_name,
                                                     self.server_list,
                                                     new_brick_list, 200):
            raise Exception("Bricks are not online")

        # Comparing brick lists of before and after performing replace brick
        # operation
        if brick_list != new_brick_list:
            raise Exception("Bricks are not same before and after running"
                            " replace brick operation")
