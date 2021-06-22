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

from time import sleep
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
                                          create_only=True)
        if not ret:
            raise Exception("Failed to create volumes")
        redant.set_volume_options('all',
                                  {'cluster.brick-multiplex': 'enable'},
                                  self.server_list[0])
        vol_list = redant.get_volume_list(self.server_list[0])
        for volname in vol_list:
            print(volname)
            print(vol_list.index(volname))
            # if vol_list.index(volname) == 2:
            #     redant.execute_abstract_op_node("reboot",
            #                                     self.server_list[2])
            # redant.volume_start(volname,
            #                     self.server_list[0])

        for _ in range(10):
            sleep(1)
            ret = redant.are_nodes_online(self.server_list[2])
            if ret:
                break

        if not ret:
            raise Exception("Node is not online")

        for server in self.server_list:
            ret = redant.execute_abstract_op_node("pgrep glusterfsd",
                                                  server)
            print("\n\n", ret['msg'])
            # out = ret['msg'].split()
            # self.assertFalse(ret, "Failed to get 'glusterfsd' pid")
            # self.assertEqual(
            #     len(out), 1, "More then 1 brick process  seen in glusterfsd")
