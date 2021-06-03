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

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

  Description:
  Test Cases in this module related to gluster bricks are online
  after node reboot or not
"""
from random import choice
from tests.d_parent_test import DParentTest


# disruptive;dist-disp
class TestCase(DParentTest):

    def check_bricks_online(self):
        # check if all the bricks are online
        for volname in self.volume_names:
            vol_bricks = self.redant.es.get_all_bricks_list(volname)
            if not (self.redant.
                    wait_for_bricks_to_come_online(volname,
                                                   self.server_list,
                                                   vol_bricks)):
                raise Exception("Unexpected: Few bricks are offline")

    def check_node_after_reboot(self, server):
        # wait for glusterd to start
        if not self.redant.wait_for_glusterd_to_start(server):
            raise Exception("Glusterd is not running")

        # wait for peers to connect
        if not (self.redant.wait_for_peers_to_connect(self.server_list,
                                                      self.server_list[0],
                                                      wait_timeout=30)):
            raise Exception("Peers are not in connected state")

    def run_test(self, redant):
        """
        Steps:
        1) Create all types of volumes
        2) Start the volume and check the bricks are online
        3) Reboot a node at random
        4) After the node is up check the bricks are online
        5) Set brick-mux to on
        6) stop and start the volume to get the brick-mux into effect
        7) Check all bricks are online
        8) Now perform node reboot
        9) After node reboot all bricks should be online
        """

        # Creating all types of volumes disperse, replicate, arbiter
        all_volumes = ['disp', 'rep', 'arb']
        self.volume_names = []
        for iteration, volume in enumerate(all_volumes):
            volname = f"{self.test_name}-{volume}-{iteration}"
            self.volume_names.append(volname)
            conf_dict = self.vol_type_inf[self.conv_dict[volume]]
            redant.setup_volume(volname, self.server_list[0],
                                conf_dict, self.server_list,
                                self.brick_roots, True)

        # Adding self.volname to the all_volumes list
        self.volume_names.append(self.vol_name)

        # Validate whether all volume bricks are online or not
        self.check_bricks_online()

        # Perform node reboot
        random_server = choice(self.server_list)
        redant.reboot_nodes(random_server)

        # Wait till node comes back online
        redant.wait_node_power_up(random_server)

        # Wait till glusterd is started on the node rebooted
        self.check_node_after_reboot(random_server)

        # After reboot check bricks are online
        self.check_bricks_online()

        # Enable brick-mux on and stop and start the volumes
        redant.set_volume_options('all',
                                  {"cluster.brick-multiplex": "enable"},
                                  self.server_list[0])

        # Stop all the volumes in the cluster
        for vol in self.volume_names:
            redant.volume_stop(vol, self.server_list[0])

        # wait till all the volumes are stopped
        for vol in self.volume_names:
            redant.wait_for_vol_to_go_offline(vol, self.server_list[0])

        # Starting the volume to get brick-mux into effect
        for vol in self.volume_names:
            redant.volume_start(vol, self.server_list[0])

        # Checking all bricks are online or not
        self.check_bricks_online()

        # Perform node reboot
        redant.reboot_nodes(random_server)

        # Wait till glusterd is started on the node rebooted
        redant.wait_node_power_up(random_server)

        # Wait till glusterd is started on the node rebooted
        self.check_node_after_reboot(random_server)

        # Validating bricks are online after node reboot
        self.check_bricks_online()
