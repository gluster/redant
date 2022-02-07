"""
 Copyright (C) 2017-2020 Red Hat, Inc. <http://www.redhat.com>

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
    Test File creation with hashed and cached subvol down scenarios

 *Flaky Test*
 Reason: Difference in file permissions due to SELinux context missing in CI
"""

# disruptive;dist-rep,dist-disp
import socket
from tests.d_parent_test import DParentTest


class TestCreateFile(DParentTest):

    def run_test(self, redant):
        '''
        test case: (file creation)
        Steps:
        - Create and start a volume
        - Mount it on a client
        - Create a file on mountpoint
        - Verify that the file is created on the hashed subvol alone
        - Verify that the trusted.glusterfs.pathinfo reflects the file location
        - Verify that the file creation fails if the hashed subvol is down
        '''
        # hash for file1
        filehash = redant.calculate_hash(self.server_list[0], 'file1')

        # collect subvol info
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")

        secondary_bricks = []
        for subvol in subvols:
            secondary_bricks.append(subvol[0])

        bricklist = []
        for item in secondary_bricks:
            bricklist.append(item)

        file_one = f"{self.mountpoint}/file1"

        # create a file
        redant.execute_abstract_op_node(f"touch {file_one}",
                                        self.client_list[0])

        # get pathinfo xattr on the file
        cmd = f"getfattr -n trusted.glusterfs.pathinfo {file_one}"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        out = "".join(ret['msg'])

        if self.volume_type == "dist":
            brickhost = (out.split(":"))[3]
            brickhost = socket.gethostbyname(brickhost)
            brickpath = (out.split(":"))[4].split(">")[0]
        else:
            brickhost = (out.split(":"))[4]
            brickhost = socket.gethostbyname(brickhost)
            brickpath = (out.split(":")[5]).split(">")[0]

        # make sure the file is present only on the hashed brick
        count = -1
        for brickdir in bricklist:
            count += 1
            ret = redant.hashrange_contains_hash(brickdir, filehash)
            host, path = brickdir.split(":")
            if ret:
                hash_subvol = subvols[count]
                redant.execute_abstract_op_node(f"stat {path}/file1", host)
                continue

            ret = redant.execute_abstract_op_node(f"stat {path}/file1",
                                                  host, False)
            if ret['error_code'] == 0:
                raise Exception("Expected stat to fail")

        # checking if pathinfo xattr has the right value
        redant.execute_abstract_op_node(f"stat {brickpath}", brickhost)

        # get permission from mount
        ret = redant.execute_abstract_op_node(f"ls -l {file_one}",
                                              self.client_list[0])
        mperm = ret['msg'][0].strip().split(" ")[0]
        if mperm is None:
            raise Exception("Unexpected: failed to get file1 permissions")

        # get permission from brick
        ret = redant.execute_abstract_op_node(f"ls -l {brickpath}",
                                              brickhost)
        bperm = ret['msg'][0].strip().split(" ")[0]
        if bperm is None:
            raise Exception("Unexpected: failed to get file1 permissions")

        # check if the permission matches
        if mperm != bperm:
            raise Exception("Expected permission to match")

        # check that gfid xattr is present on the brick
        redant.execute_abstract_op_node("getfattr -n trusted.gfid "
                                        f"{brickpath}", brickhost)

        # delete the file, bring down it's hash, create the file,
        redant.execute_abstract_op_node(f"rm -f {file_one}",
                                        self.client_list[0])

        ret = redant.bring_bricks_offline(self.vol_name, hash_subvol)
        if not ret:
            raise Exception('Error in bringing down subvolume '
                            f'{hash_subvol}')

        # check file creation should fail
        ret = redant.execute_abstract_op_node(f"touch {file_one}",
                                              self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: file creation is successful")
