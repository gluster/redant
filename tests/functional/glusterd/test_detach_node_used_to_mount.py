"""
  Copyright (C) 2019-2020  Red Hat, Inc. <http://www.redhat.com>

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

  Description:
  Detaching a node which is used to mount volume and performing
  various io operations like creation of files and checking the
  existance of those files.
"""

import traceback
from random import randint
from tests.d_parent_test import DParentTest


# disruptive;rep

class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.rebalance_stop(self.vol_name,
                                             self.server_list[0])
            if not ret:
                raise Exception("Rebalance operation failed to stop")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1.Create a 1X3 volume with only 3 nodes from the cluster.
        2.Mount volume on client node using the ip of the fourth node.
        3.Write IOs to the volume.
        4.Detach node N4 from cluster.
        5.Create a new directory on the mount point.
        6.Create a few files using the same command used in step 3.
        7.Add three more bricks to make the volume
          2x3 using add-brick command.
        8.Do a gluster volume rebalance on the volume.
        9.Create more files from the client on the mount point.
        10.Check for files on bricks from both replica sets.
        11.Create a new directory from the client on the mount point.
        12.Check for directory in both replica sets.
        """
        # Check if servers are sufficient to run the test case.
        if len(self.server_list) < 4:
            raise Exception("Servers are not sufficient to run the test")

        # Creating 100 files.
        command = ('for number in `seq 1 100`;do touch '
                   + self.mountpoint + '/file$number; done')
        redant.execute_abstract_op_node(command, self.client_list[0])

        # Detach N4 from the list.
        redant.peer_detach(self.server_list[3], self.server_list[0])

        # Creating a dir.
        command = f"mkdir -p {self.mountpoint}/dir1"
        redant.execute_abstract_op_node(command, self.client_list[0])

        # Creating 100 files.
        command = ('for number in `seq 101 200`;do touch '
                   + self.mountpoint + '/file$number; done')
        redant.execute_abstract_op_node(command, self.client_list[0])

        # Forming brick list
        brick_dict, brick_str = redant.form_brick_cmd(self.server_list,
                                                      self.brick_roots,
                                                      self.vol_name, 3, True)

        # Adding bricks
        redant.add_brick(self.vol_name, brick_str, self.server_list[0],
                         replica_count=3)

        # Start rebalance for volume.
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Creating 100 files.
        command = ('for number in `seq 201 300`;do touch '
                   + self.mountpoint + '/file$number; done')
        redant.execute_abstract_op_node(command, self.client_list[0])

        # Forming brivk list of added bricks
        brick_list = []
        for server in brick_dict:
            brick_list.append(f"{server}:{brick_dict[server][0]}")

        # Check for files on bricks.
        attempts = 10
        while attempts:
            number = str(randint(1, 300))
            for brick in brick_list:
                brick_server, brick_dir = brick.split(':')
                file_name = brick_dir+"/file" + number
                if redant.path_exists(brick_server, file_name):
                    redant.logger.info(f"Check xattr on host {brick_server} "
                                       f"for file {file_name}")
                    redant.get_fattr_list(file_name, brick_server)
            attempts -= 1

        # Creating a dir.
        command = f"mkdir -p {self.mountpoint}/dir2"
        ret = redant.execute_abstract_op_node(command, self.client_list[0],
                                              False)

        if ret['error_code'] != 0:
            attempts = 5
            while attempts:
                ret = redant.execute_abstract_op_node(command,
                                                      self.client_list[0],
                                                      False)
                if ret['error_code'] == 0:
                    break
                attempts -= 1
        if ret['error_code'] != 0:
            raise Exception("Failed to create directory dir2.")

        # Check for directory in both replica sets.
        for brick in brick_list:
            brick_server, brick_dir = brick.split(':')
            folder_name = brick_dir+"/dir2"
            if redant.path_exists(brick_server, folder_name):
                redant.logger.info("Check trusted.glusterfs.dht on host"
                                   f"{brick_server} for directory "
                                   f"{folder_name}")
                redant.get_fattr(folder_name, 'trusted.glusterfs.dht',
                                 brick_server)
