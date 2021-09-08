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
"""
from copy import deepcopy
import random
from tests.d_parent_test import DParentTest

# disruptive;dist-rep


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Create a 4*replica_count brick list
        2. Add a single brick to the volume,
           which should fail
        3. Add a non-existing brick, which should
           fail.
        4. Add a brick from a node which is not a
           part of the cluster.
        """
        # form bricks list to test add brick functionality
        rep_count = deepcopy(self.vol_type_inf['rep'])
        rep_count = rep_count['replica_count']
        num_of_bricks = 4 * rep_count

        _, self.bricks_list = redant.form_brick_cmd(self.server_list,
                                                    self.brick_roots,
                                                    self.vol_name,
                                                    num_of_bricks)
        self.bricks_list = self.bricks_list.split(' ')
        if self.bricks_list is None:
            raise Exception("Bricks list is empty")

        # Try to add a single brick to volume, which should fail as it is a
        # replicated volume, we should pass multiple of replica count number
        # of bricks
        ret = redant.add_brick(self.vol_name,
                               self.bricks_list[0],
                               self.server_list[0],
                               excep=False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Adding a single brick to "
                            "a replicated volume should fail")
        # add brick replica count number of bricks in which one is a
        # non existing brick (not using the brick used in the earlier test)
        bricks_to_add = self.bricks_list[1:rep_count + 1]
        # make one of the bricks a non-existing one (randomly)
        random_index = random.randint(0, rep_count - 1)
        bricks_to_add[random_index] += "/non_existing_brick"

        br_cmd = " ".join(bricks_to_add)
        kwargs = {'replica_count': rep_count}
        ret = redant.add_brick(self.vol_name,
                               br_cmd, self.server_list[0],
                               excep=False, **kwargs)
        if ret['msg']['opRet'] == 0:
            raise Exception("Adding a non-existing brick to "
                            "a volume should fail")

        # add a brick from a node which is not a part of the cluster
        # (not using bricks used in earlier tests)
        bricks_to_add = self.bricks_list[rep_count + 1:
                                         (2 * rep_count) + 1]
        # change one (random) brick's node name to a non existent node
        random_index = random.randint(0, rep_count - 1)
        brick_to_change = bricks_to_add[random_index].split(":")
        brick_to_change[0] = "abc.def.ghi.jkl"
        bricks_to_add[random_index] = ":".join(brick_to_change)

        br_cmd = " ".join(bricks_to_add)
        kwargs = {'replica_count': rep_count}
        ret = redant.add_brick(self.vol_name,
                               br_cmd, self.server_list[0],
                               excep=False, **kwargs)
        if ret['msg']['opRet'] == 0:
            raise Exception("Adding a brick from a node which is not "
                            "part of the cluster should fail")

        # add correct number of valid bricks, it should succeed
        # (not using bricks used in earlier tests)
        bricks_to_add = self.bricks_list[(2 * rep_count) + 1:
                                         (3 * rep_count) + 1]
        br_cmd = " ".join(bricks_to_add)
        kwargs = {'replica_count': rep_count}
        redant.add_brick(self.vol_name,
                         br_cmd, self.server_list[0],
                         False, True, **kwargs)

        # Perform rebalance start operation
        redant.rebalance_start(self.vol_name, self.server_list[0])
