"""
 Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

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
    Test data delete/rename on arbiter volume
"""

# disruptive;arb,dist-arb

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test steps:
        - Get brick list
        - Create files and rename
        - Check if brick path contains old files
        - Delete files from mountpoint
        - Check .glusterfs/indices/xattrop is empty
        - Check if brickpath is empty
        """
        # Get the bricks from the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Empty bricks list")

        # Create files and rename
        cmd = (f'cd {self.mountpoint} ;for i in `seq 1 100` ;'
               'do mkdir -pv directory$i;'
               'cd directory$i;'
               'dd if=/dev/urandom of=file$i bs=1M count=5;'
               'mv file$i renamed$i;done;')
        redant.execute_abstract_op_node(cmd,
                                        self.client_list[0])

        # Check if brickpath contains old files
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            cmd = f"ls -1 {brick_path} |grep file |wc -l "
            ret = redant.execute_abstract_op_node(cmd,
                                                  brick_node)
            if int(ret['msg'][0].rstrip("\n")) != 0:
                raise Exception(f"Brick path {brick_path} contains old"
                                f" file in node {brick_node}")

        # Delete files from mountpoint
        cmd = f'rm -rf -v {self.mountpoint}/*'
        redant.execute_abstract_op_node(cmd,
                                        self.client_list[0])
        # Check .glusterfs/indices/xattrop is empty
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            cmd = (f"ls -1 {brick_path}/.glusterfs/indices/xattrop/ | "
                   "grep -ve \"xattrop-\" | wc -l")
            ret = redant.execute_abstract_op_node(cmd,
                                                  brick_node)
            if int(ret['msg'][0].rstrip("\n")) != 0:
                raise Exception(".glusterfs/indices/xattrop"
                                " is not empty")

        # Check if brickpath is empty
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            cmd = f"ls -1 {brick_path} |wc -l "
            ret = redant.execute_abstract_op_node(cmd,
                                                  brick_node)
            if int(ret['msg'][0].rstrip("\n")) != 0:
                raise Exception(f"Brick path {brick_path} is not empty"
                                f" in node {brick_node}")
