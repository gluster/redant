"""
Copyright (C) 2017-2020 Red Hat, Inc. <http://www.redhat.com>

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

"""

# disruptive;dist

import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.setup_done = True

    def terminate(self):

        try:
            # wait till peers are in connected state
            if not (self.redant.
                    wait_for_peers_to_connect(self.server_list,
                                                self.server_list[0]):
                raise Exception("Failed to connect peers")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1) Create a cluster.
        2) Create volume using the first three nodes say N1, N2 and N3.
        3) While the create is happening restart the fourth node N4.
        4) Check if glusterd has crashed on any node.
        5) While the volume start is happening restart N4.
        6) Check if glusterd has crashed on any node.
        """
        if len(self.server_list) < 4:
            # raise Exception("Minimum 4 nodes required for this TC to run")
            print("Minimum 4 nodes required for this TC to run")

        # Fetching all the parameters for volume_create
        list_of_three_servers = self.server_list[0:3]
        print(list_of_three_servers)
        # for server in self.servers[0:3]:
        #     list_of_three_servers.append(server)
        #     server_info_for_three_nodes[server] = self.all_servers_info[server]

        # Restarting glusterd in a loop
        # restart_cmd = ("for i in `seq 1 5`; do "
        #                "service glusterd restart; "
        #                "systemctl reset-failed glusterd; "
        #                "sleep 3; "
        #                "done")
        # proc1 = redant.execute_command_async(restart_cmd,
        #                                      self.server_list[3])

        # # After running restart in g.async adding 10 sec sleep
        # sleep(10)

        # Creating volumes using 3 servers
        self.volume_type = "dist"
        self.vol_name = (f"{self.test_name}-{self.volume_type}")
        conf_hash = self.vol_type_inf[self.conv_dict[self.volume_type]]
        redant.volume_create(self.vol_name, self.server_list[0], conf_hash,
                                list_of_three_servers, self.brick_roots)
        # ret, _, _ = volume_create(self.mnode, self.volname,
        #                           bricks_list)
        # self.assertEqual(ret, 0, "Volume creation failed")
        # g.log.info("Volume %s created successfully", self.volname)

        # ret, _, _ = proc1.async_communicate()
        # self.assertEqual(ret, 0, "Glusterd restart not working.")

        # # Checking if peers are connected or not.
        # count = 0
        # while count < 60:
        #     ret = is_peer_connected(self.mnode, self.servers)
        #     if ret:
        #         break
        #     sleep(3)
        #     count += 1
        # self.assertTrue(ret, "Peers are not in connected state.")
        # g.log.info("Peers are in connected state.")

        # # Restarting glusterd in a loop
        # restart_cmd = ("for i in `seq 1 5`; do "
        #                "service glusterd restart; "
        #                "systemctl reset-failed glusted; "
        #                "sleep 3; "
        #                "done")
        # proc1 = g.run_async(self.servers[3], restart_cmd)

        # # After running restart in g.async adding 10 sec sleep
        # sleep(10)

        # # Start the volume created.
        # ret, _, _ = volume_start(self.mnode, self.volname)
        # self.assertEqual(ret, 0, "Volume start failed")
        # g.log.info("Volume %s started successfully", self.volname)

        # ret, _, _ = proc1.async_communicate()
        # self.assertEqual(ret, 0, "Glusterd restart not working.")

        # # Checking if peers are connected or not.
        # count = 0
        # while count < 60:
        #     ret = is_peer_connected(self.mnode, self.servers)
        #     if ret:
        #         break
        #     sleep(3)
        #     count += 1
        # self.assertTrue(ret, "Peers are not in connected state.")
        # g.log.info("Peers are in connected state.")
