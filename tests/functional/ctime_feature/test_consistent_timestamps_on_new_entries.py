"""
Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>
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
    This testcase tests for atime, ctime and mtime to be same when a
    file or directory is created
"""

# nonDisruptive;dist,rep,dist-rep,disp,dist-disp,arb,dist-arb
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def _validate_timestamp(self, object_path):
        stat_data = self.redant.get_file_stat(self.client_list[0], object_path)
        if stat_data is None:
            raise Exception(f"stat on {object_path} failed")
        ret = stat_data['msg']
        if ret["atime"] != ret["ctime"] != ret["mtime"]:
            raise Exception(f"a|m|c timestamps on {object_path}"
                            "are not equal")

    def run_test(self, redant):
        '''
        1. Create a volume , enable features.ctime, mount volume
        2. Create a directory "dir1" and check the a|m|c times
        3. Create a file "file1"  and check the a|m|c times
        4. Again create a new file "file2" as below
            command>>> touch file2;stat file2;stat file2
        5. Check the a|m|c times of "file2"
        6. The atime,ctime,mtime must be same within each object
        '''
        # Check if ctime feature is disabled by default and enable it
        option = redant.get_volume_options(self.vol_name, "features.ctime",
                                           self.server_list[0])
        if option['features.ctime'] == 'off':
            redant.set_volume_options(self.vol_name, {'features.ctime': 'on'},
                                      self.server_list[0])

        # Create a directory and check if ctime, mtime, atime is same
        dir_path = f"{self.mountpoint}/dir1"
        cmd = f"mkdir {dir_path}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])
        self._validate_timestamp(dir_path)

        # Create a file and check if ctime, mtime, atime is same
        file_path = f"{self.mountpoint}/file1"
        cmd = f"touch {file_path}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])
        self._validate_timestamp(file_path)

        # Create a file and issue stat immediately. This step helps in
        # testing a corner case where issuing stat immediately was changing
        # ctime before the touch was effected on the disk
        file_path2 = f"{self.mountpoint}/file2"
        cmd = f"touch {file_path2}; stat {file_path2}; stat {file_path2}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])
        self._validate_timestamp(file_path2)
