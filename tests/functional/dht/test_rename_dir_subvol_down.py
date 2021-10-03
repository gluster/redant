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
    Test for rename of directory with subvol down
"""

# disruptive;dist-rep,dist-disp
from time import sleep
from tests.d_parent_test import DParentTest


class TestRenameDir(DParentTest):

    def _create_src_and_dst_dir(self):
        """
        A function to create src and dst directory such that
        src and dst directories hashes to different sub volumes.
        """
        # Getting all the subvols.
        self.subvols = self.redant.get_subvols(self.vol_name,
                                               self.server_list[0])

        # Create srcdir
        self.redant.create_dir(self.mountpoint, "srcdir", self.client_list[0])

        # Find hashed subvol
        srchashed = self.redant.find_hashed_subvol(self.subvols, "srcdir",
                                                   "srcdir")
        if srchashed is None:
            raise Exception("Could not find hashed subvol for srcdir")
        self.srccount = srchashed[1]

        newhash = self.redant.find_new_hashed(self.subvols, "srcdir",
                                              "srcdir")
        if newhash is None:
            raise Exception("Could not find new hashed for dstdir")

        self.dstcount = newhash[2]

        # Create dstdir
        self.dstdir = f"{self.mountpoint}/{str(newhash[0])}"

        self.redant.create_dir(self.mountpoint, str(newhash[0]),
                               self.client_list[0])

    def run_test(self, redant):
        """
        Case 1: test_rename_dir_src_hashed_down
        1.mkdir srcdir and dstdir(such that srcdir and dstdir
        hashes to different subvols)
        2.Bring down srcdir hashed subvol
        3.mv srcdir dstdir (should fail)
        """
        self.srcdir = f"{self.mountpoint}/srcdir"

        # Create source and destination dir.
        self._create_src_and_dst_dir()

        # Bring down srchashed
        ret = redant.bring_bricks_offline(self.vol_name,
                                          self.subvols[self.srccount])
        if not ret:
            raise Exception('Error in bringing down subvolume '
                            f'{self.subvols[self.srccount]}')

        # Rename the directory
        cmd = f"mv {self.srcdir} {self.dstdir}"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Expected rename to fail")

        # Bring up the subvol
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         self.subvols[self.srccount])
        if not ret:
            raise Exception("Failed to bring up the bricks")

        # Sleep for 5secs to allow mount of volume
        sleep(5)

        # Cleanup mountpoint for next case
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_rename_dir_src_dst_hashed_down
        """
        Steps:
        1.mkdir srcdir dstdir (different hashes)
        2.Bring down srcdir hashed
        3.Bring down dstdir hashed
        4.mv srcdir dstdir (should fail)
        """
        # Create source and destination dir.
        self._create_src_and_dst_dir()

        # Bring down srchashed
        ret = redant.bring_bricks_offline(self.vol_name,
                                          self.subvols[self.srccount])
        if not ret:
            raise Exception('Error in bringing down subvolume '
                            f'{self.subvols[self.srccount]}')

        # Bring down dsthashed
        ret = redant.bring_bricks_offline(self.vol_name,
                                          self.subvols[self.dstcount])
        if not ret:
            raise Exception('Error in bringing down subvolume '
                            f'{self.subvols[self.dstcount]}')

        # Rename the directory (should fail)
        cmd = f"mv {self.srcdir} {self.dstdir}"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Expected rename to fail")

        # Bring up the subvol
        both_subvols = (self.subvols[self.srccount]
                        + self.subvols[self.dstcount])
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         both_subvols)
        if not ret:
            raise Exception("Failed to bring up the bricks")

        # Sleep for 5secs to allow mount of volume
        sleep(5)

        # Cleanup mountpoint for next case
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 3: test_rename_dir_dst_hashed_down
        """
        Steps:
        1.mkdir srcdir dstdir
        2.Bring down dstdir hashed subvol
        3.mv srcdir dstdir (should fail)
        """
        # Create source and destination dir.
        self._create_src_and_dst_dir()

        # Bring down dsthashed
        ret = redant.bring_bricks_offline(self.vol_name,
                                          self.subvols[self.dstcount])
        if not ret:
            raise Exception('Error in bringing down subvolume '
                            f'{self.subvols[self.dstcount]}')

        # Rename the directory
        cmd = f"mv {self.srcdir} {self.dstdir}"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Expected rename to fail")

        # Bring up the subvol
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         self.subvols[self.dstcount])
        if not ret:
            raise Exception("Failed to bring up the bricks")
