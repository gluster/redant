"""
  Copyright (C) 2018  Red Hat, Inc. <http://www.redhat.com>

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
    Add a new brick with identical name as the previous added
    brick on a new node and checking volume status.
"""

from tests.d_parent_test import DParentTest


# disruptive;
class TestCase(DParentTest):

    def run_test(self, redant):
        """
        In this test case:
        1. Create Dist Volume on Node 1
        2. Down brick on Node 1
        3. Peer Probe N2 from N1
        4. Add identical brick on newly added node
        5. Check volume status
        """

        redant.delete_cluster(self.server_list)

        # Create a distributed volume on Node1
        self.volume_type1 = 'dist'
        self.volume_name1 = f"{self.test_name}-{self.volume_type1}-1"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
        conf_dict['dist_count'] = 1
        redant.setup_volume(self.volume_name1, self.server_list[0], conf_dict,
                            [self.server_list[0]], self.brick_roots, True)

        # Getting the bricks list to bring down a brick
        redant.logger.info("Get all the bricks of the volume")
        bricks_list = redant.get_all_bricks(self.volume_name1,
                                            self.server_list[0])
        if len(bricks_list) == 0:
            raise Exception(f"Failed to fetch bricks for {self.volume_name1}")

        # Bring the brick offline
        ret = redant.bring_bricks_offline(self.volume_name1, bricks_list[0])
        if not ret:
            raise Exception("Failed to bring down the bricks")

        redant.peer_probe_servers(self.server_list[1], self.server_list[0],
                                  True)

        _, brick_str = redant.form_brick_cmd([self.server_list[1]],
                                             self.brick_roots,
                                             self.volume_name1, 1)

        # adding identical brick on different node
        redant.add_brick(self.volume_name1, brick_str,
                         self.server_list[0], True)

        redant.volume_start(self.volume_name1, self.server_list[0],
                            force=True)

        vol_status = redant.get_volume_status(self.volume_name1,
                                              self.server_list[0])

        if vol_status is None:
            raise Exception("Volume status returned None")
