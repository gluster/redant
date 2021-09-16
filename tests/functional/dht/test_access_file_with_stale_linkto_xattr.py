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
    TC to checks if the files are accessible as non-root user if
    the files have stale linkto xattr.
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestAccessFileWithStaleLinktoXattr(DParentTest):

    def terminate(self):
        """
        Delete the user
        """
        try:
            ret = self.redant.del_user(self.client_list[0], "test_user1")
            if not ret:
                raise Exception("Failed to delete user")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1) Create a volume and start it.
        2) Mount the volume on client node using FUSE.
        3) Create a file.
        4) Enable performance.parallel-readdir and
           performance.readdir-ahead on the volume.
        5) Rename the file in order to create
           a linkto file.
        6) Force the linkto xattr values to become stale by changing the dht
           subvols in the graph
        7) Login as an non-root user and access the file.
        """
        # Add a new user to the clients
        ret = redant.add_user(self.client_list[0], "test_user1")
        if not ret:
            raise Exception("Failed to add user")

        # Set password for user "test_user1"
        ret = redant.set_passwd(self.client_list[0], "test_user1", "red123")
        if not ret:
            raise Exception("Failed to set password")

        # Set permissions on the mount-point
        ret = redant.set_file_permissions(self.client_list[0],
                                          self.mountpoint, "-R 777")
        if not ret:
            raise Exception("Failed to set file permissions")

        # Creating a file on the mount-point
        cmd = (f"dd if=/dev/urandom of={self.mountpoint}/FILE-1 "
               "count=1 bs=16k")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Enable performance.parallel-readdir and
        # performance.readdir-ahead on the volume
        options = {"performance.parallel-readdir": "enable",
                   "performance.readdir-ahead": "enable"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Finding a file name such that renaming source file to it will form a
        # linkto file
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        newhash = redant.find_new_hashed(subvols, "", "FILE-1")
        if not newhash:
            raise Exception("Failed to get new_hash for the file")

        new_name = str(newhash[0])
        new_host, new_name_path = newhash[1].split(':')

        # Move file such that it hashes to some other subvol and forms linkto
        # file
        ret = redant.move_file(self.client_list[0],
                               f"{self.mountpoint}/FILE-1",
                               f"{self.mountpoint}/{new_name}")
        if not ret:
            raise Exception("Rename failed")

        # Check if "dst_file" is linkto file
        ret = redant.is_linkto_file(new_host, f"{new_name_path}{new_name}")
        if not ret:
            raise Exception("File is not a linkto file")

        # Force the linkto xattr values to become stale by changing the dht
        # subvols in the graph; for that:
        # disable performance.parallel-readdir and
        # performance.readdir-ahead on the volume
        options = {"performance.parallel-readdir": "disable",
                   "performance.readdir-ahead": "disable"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Access the file as non-root user
        cmd = f"runuser -l test_user1 -c 'ls -lR {self.mountpoint}'"
        redant.execute_abstract_op_node(cmd, self.client_list[0])
