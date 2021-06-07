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
"""
# disruptive;dist-rep

import socket
import random
from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.setup_done = True
        last_node = self.server_list[len(self.server_list)-1]
        self.redant.peer_detach(last_node, self.server_list[0])

    def run_test(self, redant):

        # # create a 2x3 volume
        conf_hash = self.vol_type_inf[self.conv_dict['dist-rep']]
        redant.setup_volume(self.vol_name, self.server_list[0],
                            conf_hash, self.server_list[:-1],
                            self.brick_roots, False, True)
        num_of_servers = len(self.server_list)

        # stop glusterd on a random node of the cluster
        random_server_index = random.randint(1, num_of_servers - 2)
        random_server = self.server_list[random_server_index]
        cmd = "systemctl stop glusterd"
        redant.execute_command_async(cmd, random_server)

        # set a option on volume, stat-prefetch on
        self.options = {"stat-prefetch": "on"}
        redant.set_volume_options(self.vol_name,
                                  self.options,
                                  self.server_list[0])

        # start glusterd on the node where glusterd is stopped
        redant.start_glusterd(random_server)

        ret = redant.wait_for_glusterd_to_start(random_server)
        if not ret:
            raise Exception(f"glusterd is not running on {random_server}")

        # volume info should be synced across the cluster
        out1 = redant.get_volume_info(self.server_list[0],
                                      self.vol_name)

        count = 0
        while count < 60:
            out2 = redant.get_volume_info(random_server,
                                          self.vol_name)
            if out1 == out2:
                break
            sleep(2)
            count += 1

        if out1 != out2:
            raise Exception("volume info is not synced")

        # stop glusterd on a random server from cluster
        random_server_index = random.randint(1, num_of_servers - 1)
        random_server = self.server_list[random_server_index]
        cmd = "systemctl stop glusterd"
        redant.execute_command_async(cmd, random_server)

        # peer probe a new node
        redant.peer_probe_servers(self.server_list[num_of_servers-1],
                                  self.server_list[0])

        # start glusterd on the node where glusterd is stopped
        redant.start_glusterd(random_server)

        ret = redant.wait_for_glusterd_to_start(random_server)
        if not ret:
            raise Exception(f"glusterd is not running on {random_server}")

        # peer status should be synced across the cluster
        list1 = redant.nodes_from_pool_list(self.server_list[0])
        if list1 is None:
            raise Exception("Failed to get nodes list in the "
                            f"from {self.server_list[0]}\n")

        # replacing ip with FQDN
        i = 0
        for node in list1:
            list1[i] = socket.getfqdn(node)
            i += 1
        list1 = sorted(list1)

        count = 0
        while count < 60:
            list2 = redant.nodes_from_pool_list(random_server)
            if list1 is None:
                raise Exception("Failed to get nodes list in the "
                                f"from {random_server}\n")
            # replacing ip with FQDN
            i = 0
            for node in list2:
                list2[i] = socket.getfqdn(node)
                i += 1

            list2 = sorted(list2)
            if list2 == list1:
                break
            sleep(2)
            count += 1

        if list1 != list2:
            raise Exception("Peer status is not "
                            "synced across the cluster")
