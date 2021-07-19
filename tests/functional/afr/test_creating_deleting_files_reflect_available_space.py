"""
Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test to find the available space after creating
    and deleting files.
"""
# disruptive;rep,dist-rep

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete([self.proc],
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        - note the current available space on the mount
        - create 1M file on the mount
        - note the current available space on the mountpoint and compare
          with space before creation
        - remove the file
        - note the current available space on the mountpoint and compare
          with space before creation
        """

        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Create 1M file on client side
        self.proc = (redant.
                     create_files(num_files=1,
                                  fix_fil_size="1M",
                                  path=self.mounts[0]['mountpath'],
                                  node=self.mounts[0]['client']))
        ret = self.redant.validate_io_procs(self.proc, self.mounts[0])
        if not ret:
            raise Exception("IO validation failed")

        # Get the current available space on the mount
        cmd = (f"df --output=avail {self.mounts[0]['mountpath']}"
               f" | grep '[0-9]'")
        ret = redant.execute_abstract_op_node(cmd,
                                              self.mounts[0]['client'])
        space_before_file_creation = int(ret['msg'][0].strip("\n"))

        # Create 1M file on client side
        self.proc = (redant.
                     create_files(num_files=1,
                                  fix_fil_size="1M",
                                  path=(f"{self.mounts[0]['mountpath']}"
                                        "/newdir"),
                                  node=self.mounts[0]['client'],
                                  base_file_name="newfile"))
        ret = self.redant.validate_io_procs(self.proc, self.mounts[0])
        if not ret:
            raise Exception("IO validation failed")

        # Get the current available space on the mount
        ret = redant.execute_abstract_op_node(cmd,
                                              self.mounts[0]['client'])
        space_after_file_creation = int(ret['msg'][0].rstrip("\n"))

        # Compare available size before creation and after creation file
        space_diff = space_before_file_creation - space_after_file_creation
        space_diff = round(space_diff / 1024)

        if space_diff != 1:
            raise Exception('Available size before creation and '
                            'after creation file is not valid')

        # Delete file on client side
        if not redant.rmdir(f"{self.mounts[0]['mountpath']}/newdir",
                            self.mounts[0]['client'], True):
            raise Exception("Failed to delete the directory")

        # Get the current available space on the mount
        ret = redant.execute_abstract_op_node(cmd,
                                              self.mounts[0]['client'])
        space_after_file_deletion = int(ret['msg'][0].rstrip("\n"))

        # Compare available size before creation and after deletion file
        space_diff = space_before_file_creation - space_after_file_deletion
        if space_diff >= 200:
            raise Exception('Available size before creation is not'
                            ' proportional to the size after deletion file')
