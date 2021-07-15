"""
Copyright (C) 2015-2016  Red Hat, Inc. <http://www.redhat.com>

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
    Test Case which tests the working of FOPS in AFR.
"""

# nonDisruptive;rep

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        * Get the bricks list
        * Create file on the mountpoint
        * Create symlink
        * Start symlink on mount and verify file type and permission.
        * Readlink to verify contents
        * Readlink to verify contents
        * Stat symlink on bricks and verify file type and permission.
        """
        self.bricks_list = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])

        if self.bricks_list is None:
            raise Exception("Unable to get the bricks list")

        # create file
        cmd = f"echo 'hello_world' > {self.mountpoint}/file.txt"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # create symlink
        cmd = f"ln -s file.txt {self.mountpoint}/symlink.txt"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # stat symlink on mount and verify file type and permission.
        path = f"{self.mountpoint}/symlink.txt"
        stat_dict = redant.get_file_stat(self.client_list[0], path)['msg']

        if stat_dict['fileType'] != 'symbolic link':
            raise Exception(f"symlink but found {stat_dict['fileType']}")
        if stat_dict['permission'] != 777:
            raise Exception("Expected 777 access but found"
                            f" {stat_dict['permission']}")

        # readlink to verify contents
        cmd = f"readlink {self.mountpoint}/symlink.txt"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])

        content = ret['msg'][0].rstrip("\n")
        if content != "file.txt":
            raise Exception(f"Readlink error: got {content}")

        # stat symlink on bricks and verify file type and permission.
        for brick in self.bricks_list:
            node, path = brick.split(':')
            filepath = f"{path}/symlink.txt"
            stat_dict = redant.get_file_stat(node, filepath)['msg']
            if stat_dict['fileType'] != 'symbolic link':
                raise Exception("Expected symlink but found "
                                f"{stat_dict['filetype']}")
