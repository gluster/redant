"""
Copyright (C) 2015-2019  Red Hat, Inc. <http://www.redhat.com>

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
    Test to check the file permissions and mode.
"""
# nonDisruptive;rep

import traceback
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def terminate(self):
        """
        Cleanup and umount volume
        """
        try:
            for mount_obj in self.mnt_list:
                self.redant.del_user(mount_obj['client'], 'qa')

            self.redant.del_user(self.server_list, 'qa')

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)

        super().terminate()

    def run_test(self, redant):
        """
        Description:
        - create file file.txt on mountpoint
        - change uid, gid and permission from client
        - check uid, gid and permission on client and all servers
        """
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Create user qa
        for mount_obj in self.mnt_list:
            if not redant.add_user(mount_obj['client'], 'qa'):
                raise Exception(f"Failed to add user in {mount_obj['client']}")

        if not redant.add_user(self.server_list, 'qa'):
            raise Exception(f"Failed to add user in {self.server_list}")
        self.bricks_list = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        if self.bricks_list is None:
            raise Exception("Failed to get the list of bricks")

        # create file
        cmd = (f"dd if=/dev/urandom of={self.mountpoint}/file.txt"
               " bs=1M count=1")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Adding servers and client in single dict to check permissions
        nodes_to_check = {}
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])

        for brick in all_bricks:
            node, brick_path = brick.split(':')
            nodes_to_check[node] = brick_path

        nodes_to_check[self.mnt_list[0]['client']] = (self.
                                                      mnt_list[0]['mountpath'])

        # check file is created on all bricks and client
        for node in nodes_to_check:
            filepath = f"{nodes_to_check[node]}/file.txt"
            stat_dict = redant.get_file_stat(node, filepath)
            if stat_dict is None:
                raise Exception(f"stat on {filepath} failed")

        # get file stat info from client
        fpath = f"{self.mnt_list[0]['mountpath']}/file.txt"
        stat_dict = redant.get_file_stat(self.client_list[0], fpath)
        if stat_dict is None:
            raise Exception(f"stat on {fpath} failed")

        if stat_dict['msg']['st_uid'] != 0:
            raise Exception("Expected uid 0 but found "
                            f"{stat_dict['msg']['st_uid']}")

        if stat_dict['msg']['st_gid'] != 0:
            raise Exception("Expected gid 0 but found "
                            f"{stat_dict['msg']['st_gid']}")

        if stat_dict['msg']['mode'] != '-rw-r--r--':
            raise Exception("Expected permission -rw-r--r-- but found"
                            f"{stat_dict['msg']['mode']}")

        # change uid, gid and permission from client
        cmd = f"chown qa {fpath}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f"chgrp qa {fpath}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f"chmod 777 {fpath}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Verify that the changes are successful on bricks and client
        for node in nodes_to_check:
            fpath = f"{nodes_to_check[node]}/file.txt"

            stat_dict = redant.get_file_stat(node, fpath)

            if stat_dict is None:
                raise Exception(f"stat on {fpath} failed")

            if stat_dict['msg']['user'] != 'qa':
                raise Exception("Expected qa but found "
                                f"{stat_dict['msg']['user']}")

            if stat_dict['msg']['group'] != 'qa':
                raise Exception("Expected qa but found "
                                f"{stat_dict['msg']['group']}")

            if stat_dict['msg']['mode'] != '-rwxrwxrwx':
                raise Exception("Expected -rwxrwxrwx but found "
                                f"{stat_dict['msg']['mode']}")
