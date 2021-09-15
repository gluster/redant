"""
 Copyright (C) 2018-2020 Red Hat, Inc. <http://www.redhat.com>

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
    Test file access with subvol down
"""

# disruptive;dist,dist-disp,dist-rep
from tests.d_parent_test import DParentTest


class TestFileAccessSubvolDown(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        - Get the subvols
        - Create a file on the mountpoint
        - Find hashed subvol
        - Rename the file such that new name hashes to a new subvol
        - Check the dst hashed subvol is a linkto file
        - Check that the src hashed subvol is a data file
        - Bring down the hashed subvol
        - Create a temp mountpoint on server and do temp mount
        - Check that file is accessible
        - Cleanup temp mount
        - Bring up the hashed subvol
        - Bring down the cached subvol
        - File access should fail
        """
        # get subvol list
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols")

        # create a file
        srcfile = f"{self.mountpoint}/testfile"
        redant.execute_abstract_op_node(f"touch {srcfile}",
                                        self.client_list[0])

        # find hashed subvol
        srchashed, scount = redant.find_hashed_subvol(subvols, "",
                                                      "testfile")
        if not srchashed:
            raise Exception("Could not find srchashed")

        # rename the file such that the new name hashes to a new subvol
        newhash = redant.find_new_hashed(subvols, "", "testfile")
        if not newhash:
            raise Exception("Could not find new hashed for dstfile")

        dstname = str(newhash[0])
        dstfile = f"{self.mountpoint}/{dstname}"
        dsthashed = newhash[1]
        dcount = newhash[2]
        redant.execute_abstract_op_node(f"mv {srcfile} {dstfile}",
                                        self.client_list[0])

        # check that on dsthash_subvol the file is a linkto file
        node, brick = dsthashed.split(":")
        # '/' not needed as the 'brick' will already have '/'in the end
        filepath = f"{brick}{dstname}"
        file_stat = redant.get_file_stat(node, filepath)
        if file_stat['msg']['permission'] != 1000:
            raise Exception("Expected file permission to be 1000"
                            f" on subvol {node}")

        # check on srchashed the file is a data file
        host, brick = srchashed.split(':')
        # '/' not needed as the 'brick' will already have '/'in the end
        filepath = f"{brick}{dstname}"
        file_stat = redant.get_file_stat(host, filepath)
        if file_stat['msg']['permission'] == 1000:
            raise Exception("Expected file permission not to be 1000"
                            f" on subvol {host}")

        # Bring down the hashed subvol of dstfile(linkto file)
        ret = redant.bring_bricks_offline(self.vol_name, subvols[dcount])
        if not ret:
            raise Exception("Error in bringing down subvolume")

        # Need to access the file through a fresh lookup through a new mount
        # create a new dir(choosing server to do a mount)
        redant.execute_abstract_op_node("mkdir -p /mnt/tmp_mount",
                                        self.server_list[0])

        # do a temp mount
        redant.volume_mount(self.server_list[0], self.vol_name,
                            "/mnt/tmp_mount", self.server_list[0])

        # check that file is accessible (stat)
        redant.execute_abstract_op_node(f"stat /mnt/tmp_mount/{dstname}",
                                        self.server_list[0])

        # cleanup temporary mount
        redant.volume_unmount(self.vol_name, "/mnt/tmp_mount",
                              self.server_list[0])

        # Bring up the hashed subvol
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         subvols[dcount])
        if not ret:
            raise Exception("Error in bringing back subvol online")

        # now bring down the cached subvol
        ret = redant.bring_bricks_offline(self.vol_name, subvols[scount])
        if not ret:
            raise Exception('Error in bringing down subvolume')

        # file access should fail
        ret = redant.execute_abstract_op_node(f"stat {dstfile}",
                                              self.client_list[0],
                                              excep=False)
        if ret['error_code'] == 0:
            raise Exception(f"stat should have failed for file {dstfile}")
