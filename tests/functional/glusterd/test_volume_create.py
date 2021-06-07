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
  Test glusterd behavior with the gluster volume create command
"""

import random
from tests.d_parent_test import DParentTest


# disruptive;dist
class TestCase(DParentTest):

    def run_test(self, redant):
        """
        In this test case, volume create operations such as creating volume
        with non existing brick path, already used brick, already existing
        volume name, bring the bricks to online with volume start force,
        creating a volume with bricks in another cluster, creating a volume
        when one of the brick node is down are validated.
        """
        # Check for 4 servers
        if len(self.server_list) < 4:
            raise Exception("The test case requires 4 servers to run the test")

        # create and start a volume

        self.volume_type1 = 'dist'
        self.volume_name1 = f"{self.test_name}-{self.volume_type1}-1"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
        brick_dict, brick_cmd = redant.form_brick_cmd(self.server_list,
                                                      self.brick_roots,
                                                      self.volume_name1, 4)
        redant.volume_create_with_custom_bricks(self.volume_name1,
                                                self.server_list[0],
                                                conf_dict, brick_cmd,
                                                brick_dict)
        redant.volume_start(self.volume_name1, self.server_list[0])

        # bring a brick down and volume start force should bring it to online
        redant.logger.info("Get all the bricks of the volume")
        bricks_list = redant.es.get_all_bricks_list(self.volume_name1)
        if len(bricks_list) == 0:
            raise Exception("Failed to get the brick list")

        ret = redant.bring_bricks_offline(self.volume_name1, bricks_list[0:2])
        if not ret:
            raise Exception("Failed to bring down the bricks")

        ret = redant.volume_start(self.volume_name1, self.server_list[0],
                                  force=True)

        ret = redant.wait_for_bricks_to_come_online(self.volume_name1,
                                                    self.server_list,
                                                    bricks_list)
        if not ret:
            raise Exception("Failed to bring the bricks online")

        # create volume with previously used bricks and different volume name
        self.volume_type2 = 'dist'
        self.volume_name2 = f"{self.test_name}-{self.volume_type2}-2"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type2]]
        try:
            redant.volume_create_with_custom_bricks(self.volume_name2,
                                                    self.server_list[0],
                                                    conf_dict, brick_cmd,
                                                    brick_dict)
            raise Exception("Unexpected: Successfully created the volume "
                            "with previously used bricks")
        except Exception:
            redant.logger.info("Expected: Failed to create a volume "
                               "with previously used bricks.")

        # create a volume with already existing volume name
        try:
            redant.setup_volume(self.volume_name1, self.server_list[0],
                                conf_dict, self.server_list,
                                self.brick_roots, True)
            raise Exception("Unexpected: Successfully created the volume with "
                            "already existing volname")
        except Exception:
            redant.logger.info("Expected: Failed to create the volume with "
                               "already existing volname")

        # creating a volume with non existing brick path should fail
        self.volume_type3 = 'dist'
        self.volume_name3 = f"{self.test_name}-{self.volume_type3}-3"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type2]]
        brick_dict, brick_cmd = redant.form_brick_cmd(self.server_list,
                                                      self.brick_roots,
                                                      self.volume_name3, 2)
        non_exist_path = ":/brick/non_existing_path"
        non_existing_brick = " " + str(self.server_list[0]) + non_exist_path
        brick_cmd += non_existing_brick

        try:
            redant.volume_create_with_custom_bricks(self.volume_name3,
                                                    self.server_list[0],
                                                    conf_dict, brick_cmd,
                                                    brick_dict)
            raise Exception("Unexpected: Successfully created the volume "
                            "with non existing brick path")
        except Exception:
            redant.logger.info("Expected: Failed to create the volume with "
                               "non existing brick path")

        # cleanup the volume and peer detach all servers. form two clusters,try
        # to create a volume with bricks whose nodes are in different clusters

        # cleanup volumes
        vol_list = redant.es.get_volnames()
        if vol_list is None:
            raise Exception("Failed to get the volume list")

        for volume in vol_list:
            redant.cleanup_volume(volume, self.server_list[0])

        # peer detach all servers
        redant.delete_cluster(self.server_list)

        # form cluster 1
        redant.peer_probe(self.server_list[1], self.server_list[0])

        # form cluster 2
        redant.peer_probe(self.server_list[3], self.server_list[2])

        # Creating a volume with bricks which are part of another
        # cluster should fail
        try:
            redant.setup_volume(self.volume_name3, self.server_list[0],
                                conf_dict, self.server_list,
                                self.brick_roots, True)
            raise Exception("Unexpected: Successfully created the volume "
                            "with bricks which are part of another cluster")
        except Exception:
            redant.logger.info("Expected: Failed to create the volume with "
                               "bricks which are part of another cluster")

        # form a cluster, bring a node down. try to create a volume when one of
        # the brick node is down
        ret = redant.peer_detach(self.server_list[3], self.server_list[2])

        ret = redant.peer_probe_servers(self.server_list, self.server_list[0])

        # Taking random node from the first four nodes as the
        # volume getting created is using first four nodes
        # Excluding server_list[0]
        first_four_servers = self.server_list[:4]
        random_server = random.choice(first_four_servers[1:])
        ret = redant.stop_glusterd(random_server)

        self.volume_type4 = 'dist'
        self.volume_name4 = f"{self.test_name}-{self.volume_type4}-4"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type4]]
        try:
            redant.setup_volume(self.volume_name4, self.server_list[0],
                                conf_dict, self.server_list,
                                self.brick_roots, True)
            raise Exception("Unexpected: Successfully created the volume "
                            "with brick whose node is down")
        except Exception:
            redant.logger.info("Expected: Failed to create the volume with "
                               "brick whose node is down")
