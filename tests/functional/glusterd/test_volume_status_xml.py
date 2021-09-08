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
    Test volume status before and after volume start.
"""

from copy import deepcopy
from tests.d_parent_test import DParentTest

# disruptive;


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test Steps:
        1. Create a two node cluster.
        2. Create 1 node distribute volume.
        3. Query for volume status with and without xml options, there
        should be no reply.
        4. Start the volume.
        5. Query volume status again.
        """

        # create a two node cluster
        cluster_nodes = self.server_list[:2]
        redant.create_cluster(cluster_nodes)
        redant.wait_till_all_peers_connected(cluster_nodes)

        # create a distributed volume with single node
        volume_type = 'dist'
        conf_hash = deepcopy(self.vol_type_inf[volume_type])
        conf_hash['dist_count'] = 1
        redant.volume_create(self.vol_name, self.server_list[0],
                             conf_hash, self.server_list,
                             self.brick_roots, True)

        # Get volume status
        cmd = f'gluster vol status {self.vol_name}'
        ret = redant.execute_command(cmd, self.server_list[0])
        if ret['error_msg'] != f'Volume {self.vol_name} is not started\n':
            raise Exception("Volume status erraneous")

        ret = redant.get_volume_status(self.vol_name, self.server_list[0],
                                       excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Volume status should have failed as"
                            " the volume is not started")

        # Start the volume
        redant.volume_start(self.vol_name, self.server_list[0])

        cmd = f'gluster vol status {self.vol_name}'
        ret = redant.execute_command(cmd, self.server_list[0])
        if ret['error_code'] != 0:
            raise Exception("Volume status erraneous")

        # Get volume status with --xml
        redant.get_volume_status(self.vol_name, self.server_list[0])
