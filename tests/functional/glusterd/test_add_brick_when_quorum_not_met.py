"""
 Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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

 This test checks for the add brick functionality when quorum is not met.
"""

from time import sleep
from tests.d_parent_test import DParentTest

# disruptive;dist


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Create and start a volume.
        2. Set the volume options :
             {'cluster.server-quorum-type': 'server'}
        3. Stop glusterd in half of the nodes in server list
        4. Confirm glusterd is not running in those servers
        5. Get volume status
        6. Check if bricks are offline
        7. Add brick which should fail
        8. Set the volume options :
             {'cluster.server-quorum-type': 'none'}
        9. Check if glusterd is running,
            if not then start glusterd on that node
        10. Validate peers are connected
        """

        # set cluster.server-quorum-type as server
        redant.set_volume_options(self.vol_name,
                                  {'cluster.server-quorum-type': 'server'},
                                  self.server_list[0])

        # Setting quorum ratio to 95%
        redant.set_volume_options('all',
                                  {'cluster.server-quorum-ratio': '95%'},
                                  self.server_list[0])

        # bring down glusterd of half nodes
        num_of_servers = len(self.server_list)
        num_of_nodes_to_bring_down = num_of_servers//2

        for node in range(num_of_nodes_to_bring_down, num_of_servers):
            redant.stop_glusterd(self.server_list[node])

        for node in range(num_of_nodes_to_bring_down, num_of_servers):
            ret = redant.wait_for_glusterd_to_stop(self.server_list[node])
            if not ret:
                raise Exception(f"Error: glusterd is still running on "
                                f"{self.server_list[node]}")

        # Verifying node count in volume status after glusterd stopped
        # on half of the servers, Its not possible to check the brick status
        # immediately in volume status after glusterd stop
        for _ in range(100):
            vol_status = redant.get_volume_status(self.vol_name,
                                                  self.server_list[0])
            active_servers = []
            for node in vol_status[self.vol_name]['node']:
                if node['hostname'] not in active_servers:
                    active_servers.append(node['hostname'])

            if len(active_servers) == (num_of_servers
                                       - num_of_nodes_to_bring_down):
                break
            sleep(2)

        # confirm that quorum is not met, brick process should be down
        all_bricks = redant.es.get_all_bricks_list(self.vol_name)
        bricks_to_check = all_bricks[0:num_of_nodes_to_bring_down]
        ret = redant.are_bricks_offline(self.vol_name, bricks_to_check,
                                        self.server_list[0])
        if not ret:
            raise Exception("Unexpected: Server quorum is met, "
                            "Few bricks are up")
        mul_factor = 1
        _, br_cmd = redant.form_brick_cmd(self.server_list,
                                          self.brick_roots, self.vol_name,
                                          mul_factor, True)
        ret = redant.add_brick(self.vol_name, br_cmd, self.server_list,
                               excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Add brick should have failed")

        ret = redant.check_if_bricks_list_changed(all_bricks, self.vol_name,
                                                  self.server_list[0])

        if ret:
            raise Exception("Unexpected: Bricks were added.")
