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
    TC to check volume operations
"""

import random
import re
import os
import copy
import traceback
from tests.d_parent_test import DParentTest

# disruptive;dist


class TestVolumeCreate(DParentTest):

    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.setup_done = True
        conf_hash = self.vol_type_inf[self.conv_dict[self.volume_type]]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, False, True)

    def terminate(self):
        """
        Delete the brick directory created at the root path
        """
        try:
            if self.brick_created_at_root_dir:
                cmd = f"rm -rf {self.root_brickpath.split(':')[1]}"
                self.redant.execute_abstract_op_node(cmd,
                                                     self.brick_root_node)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):

        self.brick_created_at_root_dir = False

        # Get brick list
        bricks_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to get the brick list")

        # remove brick path in one node and try to start the volume with force
        # and without force
        index_of_node = random.randint(0, len(bricks_list) - 1)
        brick_node, brick_path = bricks_list[index_of_node].split(":")
        cmd = f"rm -rf {brick_path}"
        redant.execute_abstract_op_node(cmd, brick_node)

        ret = redant.volume_start(self.vol_name, self.server_list[0], False,
                                  False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Volume start without force should have failed")

        ret = redant.volume_start(self.vol_name, self.server_list[0], True,
                                  False)
        if ret['msg']['opRet'] != '0':
            raise Exception("Volume start with force should have succeeded")

        # volume start force should not bring the brick online
        ret = redant.are_bricks_online(self.vol_name,
                                       bricks_list[index_of_node],
                                       self.server_list[0])
        if ret:
            raise Exception("Volume start shouldn't have brought the bricks"
                            " online")

        # Delete the volume
        redant.cleanup_volume(self.vol_name, self.server_list[0])

        # Merged TC test_volume_create_on_brick_root

        self.volume1 = "second_volume"
        num_of_bricks = len(self.server_list)
        brick_dict, brick_cmd = redant.form_brick_cmd(self.server_list,
                                                      self.brick_roots,
                                                      self.volume1,
                                                      num_of_bricks)

        # Save bricks list to use it later
        same_brick_cmd = copy.deepcopy(brick_cmd)
        same_brick_dict = copy.deepcopy(brick_dict)

        brick_list = brick_cmd.split(" ")
        complete_brick = brick_list[0].split(":")
        brick_root = os.path.dirname(complete_brick[1])
        self.root_brickpath = f"{complete_brick[0]}:{brick_root}-b1"
        self.brick_root_node = complete_brick[0]
        brick_list[0] = self.root_brickpath
        brick_cmd = " ".join(brick_list)
        brick_dict[complete_brick[0]] = [self.root_brickpath]

        conf_hash = {
            "dist_count": 3,
            "replica_count": 1,
            "transport": "tcp"
        }

        ret = redant.volume_create_with_custom_bricks(self.volume1,
                                                      self.server_list[0],
                                                      conf_hash, brick_cmd,
                                                      brick_dict, False,
                                                      False)
        if ret['error_code'] == 0:
            raise Exception("Volume creation at root brick path should have"
                            " failed")

        self.brick_created_at_root_dir = True

        # Volume creation with force should succeed
        ret = redant.volume_create_with_custom_bricks(self.volume1,
                                                      self.server_list[0],
                                                      conf_hash, brick_cmd,
                                                      brick_dict, True,
                                                      False)
        if ret['error_code'] != 0:
            raise Exception("Volume creation at root brick path should have"
                            " succeeded")

        # Create a sub-directory under root partition and create a volume
        self.volume2 = "third_volume"

        sub_dir_path = f"{brick_root}/sub_dir"
        cmd = f"mkdir {sub_dir_path}"
        redant.execute_abstract_op_node(cmd, self.server_list[0])
        sub_dir_brick_node = brick_list[0].split(":")[0]
        sub_dir_brick = f"{sub_dir_brick_node}:{sub_dir_path}"
        brick_list[0] = sub_dir_brick
        brick_cmd = " ".join(brick_list)
        brick_dict[sub_dir_brick_node] = [sub_dir_path]

        # Volume create with used bricks should fail
        ret = redant.volume_create_with_custom_bricks(self.volume2,
                                                      self.server_list[0],
                                                      conf_hash, brick_cmd,
                                                      brick_dict, True,
                                                      False)
        if ret['error_code'] == 0:
            raise Exception("Volume creation with used brick path should have"
                            " failed")

        # delete the volume created on root partitiion and clear all
        # attributes. now volume creation should succeed
        redant.volume_delete(self.volume1, self.server_list[0])

        for brick in brick_list:
            node, brick_path = brick.split(":")
            brick_root = os.path.dirname(brick_path)
            cmd1 = f"rm -rf {brick_root}/*"
            cmd2 = f"getfattr -d -m . {brick_root}/"
            cmd3 = f"setfattr -x trusted.glusterfs.volume-id {brick_root}/"
            cmd4 = f"setfattr -x trusted.gfid {brick_root}/"
            redant.execute_abstract_op_node(cmd1, node)
            ret = redant.execute_abstract_op_node(cmd2, node)
            if re.search("trusted.glusterfs.volume-id", " ".join(ret['msg'])):
                redant.execute_abstract_op_node(cmd3, node)
            if re.search("trusted.gfid", " ".join(ret['msg'])):
                redant.execute_abstract_op_node(cmd4, node)

        # creation of volume should succeed
        redant.volume_create_with_custom_bricks(self.volume1,
                                                self.server_list[0],
                                                conf_hash, same_brick_cmd,
                                                same_brick_dict, False,
                                                False)

        # Delete the volume
        redant.volume_delete(self.volume1, self.server_list[0])

        # Merged TC test_volume_op

        # Starting a non existing volume should fail
        ret = redant.volume_start("no_vol", self.server_list[0], True, False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Expected: It should fail to Start a non"
                            " existing volume. Actual: Successfully started "
                            "a non existing volume")

        # Stopping a non existing volume should fail
        ret = redant.volume_stop("no_vol", self.server_list[0], True, False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Expected: It should fail to stop "
                            "non-existing volume. Actual: Successfully "
                            "stopped a non existing volume")

        # Deleting a non existing volume should fail
        ret = redant.volume_delete("no_vol", self.server_list[0], False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Expected: It should fail to delete a "
                            "non existing volume. Actual:Successfully deleted"
                            " a non existing volume")

        # Detach a server and try to create volume with node
        # which is not in cluster
        redant.peer_detach(self.server_list[1], self.server_list[0])

        self.volume3 = "fourth-volume"
        num_of_bricks = len(self.server_list)
        brick_dict, brick_cmd = redant.form_brick_cmd(self.server_list,
                                                      self.brick_roots,
                                                      self.volume3,
                                                      num_of_bricks)

        ret = redant.volume_create_with_custom_bricks(self.volume3,
                                                      self.server_list[0],
                                                      conf_hash, brick_cmd,
                                                      brick_dict, False,
                                                      False)
        if ret['error_code'] == 0:
            raise Exception("Successfully created volume with brick "
                            "from which is not a part of node")

        # Peer probe the detached server
        redant.peer_probe(self.server_list[1], self.server_list[0])

        # Wait for peer to connect
        if not redant.wait_for_peers_to_connect(self.server_list[1],
                                                self.server_list[0]):
            raise Exception("Peers are not in connected state")

        # Remove the brick directories created above
        brick_list = brick_cmd.split(" ")
        for brick in brick_list:
            brick_node, brick_path = brick.split(":")
            cmd = f"rm -rf {brick_path}"
            redant.execute_abstract_op_node(cmd, brick_node)

        # Create and start a volume
        redant.volume_create_with_custom_bricks(self.volume3,
                                                self.server_list[0],
                                                conf_hash, brick_cmd,
                                                brick_dict)

        redant.volume_start(self.volume3, self.server_list[0])

        # Starting already started volume should fail
        ret = redant.volume_start(self.volume3, self.server_list[0], False,
                                  False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Expected: It should fail to start a "
                            "already started volume. Actual:Successfully"
                            " started a already started volume ")

        # Deleting a volume without stopping should fail
        ret = redant.volume_delete(self.volume3, self.server_list[0],
                                   False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Expected: It should fail to delete a volume"
                            " without stopping. Actual: Successfully "
                            "deleted a volume without stopping it")

        # Stopping a volume should succeed
        redant.volume_stop(self.volume3, self.server_list[0])

        # Stopping a already stopped volume should fail
        ret = redant.volume_stop(self.volume3, self.server_list[0], False,
                                 False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Expected: It should fail to stop a "
                            "already stopped volume . Actual: Successfully"
                            "stopped a already stopped volume")

        # Deleting a volume should succeed
        redant.volume_delete(self.volume3, self.server_list[0])

        # Deleting an already deleted volume should fail
        ret = redant.volume_delete(self.volume3, self.server_list[0],
                                   False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Expected: It should fail to delete an already"
                            " deleted volume. Actual: Successfully "
                            "deleted a volume which is already deleted")

        # Volume info command should succeed
        ret = redant.get_volume_info(self.server_list[0])
        if ret is None:
            raise Exception("Volume info command failed")
