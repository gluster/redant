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

You should have received a copy of the GNU General Public License along`
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# nonDisruptive;dist-rep,dist-arb,dist-disp,dist

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume and start it.
        2. Mount the volume using FUSE.
        3. Create multiple level of dirs and files inside every dir.
        4. Rename files such that linkto files are created.
        5. From the mount point do an rm -rf * and check if all files
           are delete or not from mount point as well as backend bricks.
        """
        # Fetch timestamp to check for core files
        ret = redant.execute_abstract_op_node('date +%s', self.server_list[0])
        test_timestamp = ret['msg'][0].rstrip('\n')

        # Create multiple level of dirs and files inside every dir
        cmd = (f"cd {self.mountpoint};"
               "for i in seq `1 100`; do mkdir dir$i; cd dir$i; "
               "for j in seq `1 200`; do dd if=/dev/urandom of=file$j bs=1K"
               " count=1; done; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Rename files such that linkto files are created
        cmd = (f"cd {self.mountpoint}; "
               "for i in seq `1 100`; do cd dir$i; "
               "for j in seq `1 200`; do mv file$j ntfile$j; done; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # From the mount point do an rm -rf * and check if all files
        # are delete or not from mount point as well as backend bricks.
        cmd = (f"rm -rf {self.mountpoint}/*")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        ret = redant.get_dir_contents(self.mountpoint, self.client_list[0])
        if ret:
            raise Exception("Mountpoint is not empty")

        for brick in redant.get_all_bricks(self.vol_name, self.server_list[0]):
            node, brick_path = brick.split(":")
            ret = redant.get_dir_contents(brick_path, node)
            if ret:
                raise Exception("Bricks are not empty")

        # Check for core file on servers and clients
        servers = self.server_list + self.client_list
        ret = redant.check_core_file_exists(servers, test_timestamp)
        if ret:
            raise Exception("glusterd service should not have crashed")
