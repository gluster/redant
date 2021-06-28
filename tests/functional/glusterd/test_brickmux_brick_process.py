"""
 Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
 [Brick-mux] Observing multiple brick processes on node reboot with
 volume start
"""
# disruptive;

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Create a 3 node cluster.
        2. Set cluster.brick-multiplex to enable.
        3. Create 15 volumes of type replica 1x3.
        4. Start all the volumes one by one.
        5. While the volumes are starting reboot one node.
        6. check for pidof glusterfsd single process should be visible
        """

        redant.delete_cluster(self.server_list)

        redant.create_cluster(self.server_list[:3])
        conf_dict = self.vol_type_inf[self.conv_dict["rep"]]
        volname = f"{self.test_name}"
        # Volume Creation
        ret = redant.bulk_volume_creation(self.server_list[0], 3,
                                          volname, conf_dict,
                                          self.server_list[:3],
                                          self.brick_roots,
                                          create_only=True, excep=False)
        if not ret:
            raise Exception("Failed to create volumes")
        redant.set_volume_options('all',
                                  {'cluster.brick-multiplex': 'enable'},
                                  self.server_list[0])
        vol_list = redant.get_volume_list(self.server_list[0])
        for volname in vol_list:
            if vol_list.index(volname) == 2:
                redant.reboot_nodes(self.server_list[2])

            redant.volume_start(volname,
                                self.server_list[0])

        if not redant.wait_node_power_up(self.server_list[2]):
            raise Exception(f"Node {self.server_list[2]} not yet up")

        if not redant.wait_till_all_peers_connected(self.server_list):
            raise Exception("Some peers not yet connected")
        for server in self.server_list:
            out = redant.get_brick_processes_count(server)
            if out is not None and out != 1:
                raise Exception("More then 1 brick process seen in glusterfsd")
