"""
Copyright (C) 2016-2017  Red Hat, Inc. <http://www.redhat.com>

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
This test case tests various add brick scenarios
from glusto.core import Glusto as g
from glustolibs.gluster.gluster_base_class import GlusterBaseClass, runs_on
from glustolibs.gluster.exceptions import ExecutionError
from glustolibs.gluster.volume_libs import setup_volume, cleanup_volume
from glustolibs.gluster.volume_ops import (get_volume_list)
from glustolibs.gluster.brick_ops import add_brick
from glustolibs.gluster.lib_utils import form_bricks_list
from glustolibs.gluster.rebalance_ops import rebalance_start
from glustolibs.gluster.brick_libs import delete_bricks
"""
import random
from tests.d_parent_test import DParentTest

# disruptive;dist-rep


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Setup a volume
        2. Create a 4*replica_count brick list
        3. Add a single brick to the volume, 
           which should fail
        4. Add a non-existing brick, which should
           fail.
        5. Add a brick from a node which is not a
           part of the cluster.
        """
        # form bricks list to test add brick functionality
        rep_count = self.vol_type_inf[self.conv_dict['rep']]
        rep_count = rep_count['replica_count']
        print(rep_count)
        num_of_bricks = 4 * rep_count
        print(num_of_bricks)
        # self.bricks_list = form_bricks_list(self.mnode, self.volname,
        #                                     num_of_bricks,
        #                                     self.servers,
        #                                     self.all_servers_info)
        # self.assertIsNotNone(self.bricks_list, "Bricks list is None")

        # # Try to add a single brick to volume, which should fail as it is a
        # # replicated volume, we should pass multiple of replica count number
        # # of bricks
        # self.assertNotEqual(
        #     add_brick(self.mnode, self.volname, self.bricks_list[0])[0], 0,
        #     "Expected: It should fail to add a single brick to a replicated "
        #     "volume. Actual: Successfully added single brick to volume")
        # g.log.info("Failed to add a single brick to replicated volume "
        #            "(as expected)")

        # # add brick replica count number of bricks in which one is a
        # # non existing brick (not using the brick used in the earlier test)
        # kwargs = {'replica_count': replica_count_of_volume}
        # bricks_to_add = self.bricks_list[1:replica_count_of_volume + 1]
        # # make one of the bricks a non-existing one (randomly)
        # random_index = random.randint(0, replica_count_of_volume - 1)
        # bricks_to_add[random_index] += "/non_existing_brick"

        # self.assertNotEqual(
        #     add_brick(self.mnode, self.volname, bricks_to_add, **kwargs)[0], 0,
        #     "Expected: It should fail to add a non existing brick to volume. "
        #     "Actual: Successfully added a non existing brick to volume")
        # g.log.info("Failed to add a non existing brick to volume "
        #            "(as expected)")

        # # add a brick from a node which is not a part of the cluster
        # # (not using bricks used in earlier tests)
        # bricks_to_add = self.bricks_list[replica_count_of_volume + 1:
        #                                  (2 * replica_count_of_volume) + 1]
        # # change one (random) brick's node name to a non existent node
        # random_index = random.randint(0, replica_count_of_volume - 1)
        # brick_to_change = bricks_to_add[random_index].split(":")
        # brick_to_change[0] = "abc.def.ghi.jkl"
        # bricks_to_add[random_index] = ":".join(brick_to_change)
        # self.assertNotEqual(
        #     add_brick(self.mnode, self.volname, bricks_to_add, **kwargs)[0], 0,
        #     "Expected: It should fail to add brick from a node which is not "
        #     "part of a cluster. Actual: Successfully added bricks from node "
        #     "which is not a part of cluster to volume")
        # g.log.info("Failed to add bricks from node which is not a part of "
        #            "cluster to volume (as expected)")

        # # add correct number of valid bricks, it should succeed
        # # (not using bricks used in earlier tests)
        # bricks_to_add = self.bricks_list[(2 * replica_count_of_volume) + 1:
        #                                  (3 * replica_count_of_volume) + 1]
        # self.assertEqual(
        #     add_brick(self.mnode, self.volname, bricks_to_add, **kwargs)[0], 0,
        #     "Failed to add the bricks to the volume")
        # g.log.info("Successfully added bricks to volume")

        # # Perform rebalance start operation
        # self.assertEqual(rebalance_start(self.mnode, self.volname)[0], 0,
        #                  "Rebalance start failed")
