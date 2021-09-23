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
    TC to check the dht layouts of files and directories,
    along with their symlinks.
"""

# disruptive;rep,dist,dist-rep,arb,dist-arb,disp,dist-disp
from common.ops.gluster_ops.constants import TEST_LAYOUT_IS_COMPLETE
from re import search
from tests.d_parent_test import DParentTest


class TestDhtClass(DParentTest):

    def run_test(self, redant):
        """
        Case 1: test_create_directory
        Steps:
        - Create a directory on mountpoint
        - List the created directory
        - Create nested directories within the previous directory
        - Validate LAYOUT_IS_COMPLETE
        - List fattrs of the directory
        - Validate 'trusted.glusterfs.pathinfo' xattr
        """
        redant.create_dir(self.mountpoint, "/root_dir/test_dir{1..3}",
                          self.client_list[0])

        cmd = f"ls {self.mountpoint}/root_dir"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = (f"touch {self.mountpoint}/root_dir/test_file{{1..5}} "
               f"{self.mountpoint}/root_dir/test_dir{{1..3}}/test_file"
               "{{1..5}}")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f"ls {self.mountpoint}/root_dir"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])

        list_of_files_and_dirs = "".join(ret['msg']).split('\n')
        flag = True
        for x_count in range(3):
            dir_name = f'test_dir{x_count+1}'
            if dir_name not in list_of_files_and_dirs:
                flag = False
        for x_count in range(5):
            file_name = f'test_file{x_count+1}'
            if file_name not in list_of_files_and_dirs:
                flag = False
        if not flag:
            raise Exception("ls command didn't list all the "
                            "directories and files")

        cmd = f'cd {self.mountpoint}; find root_dir -type d -print'
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])

        list_of_all_dirs = "".join(ret['msg']).split('\n')
        del list_of_all_dirs[-1]

        flag = redant.validate_files_in_dir(self.client_list[0],
                                            f"{self.mountpoint}/root_dir",
                                            test_type=TEST_LAYOUT_IS_COMPLETE)
        if not flag:
            raise Exception("Layout has some holes or overlaps")

        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        for direc in list_of_all_dirs:
            list_of_gfid = []
            for brick in brick_list:
                host, brick_path = brick.split(':')
                gfid = redant.get_fattr(f"{brick_path}/{direc}",
                                        'trusted.gfid', host)
                gfid = gfid[1].split('=')[1].strip()
                list_of_gfid.append(gfid[1:-1])

            flag = True
            for x_count in range(len(list_of_gfid) - 1):
                if list_of_gfid[x_count] != list_of_gfid[x_count + 1]:
                    flag = False
            if not flag:
                raise Exception(f"The gfid for the directory {direc} is not "
                                "same on all the bricks")

        for direc in list_of_all_dirs:
            xattr_list = redant.get_fattr_list(f"{self.mountpoint}/{direc}",
                                               self.client_list[0])
            if 'security.selinux' in xattr_list:
                del xattr_list['security.selinux']
            if xattr_list:
                raise Exception("one or more xattr being displayed on mount"
                                " point")

        for direc in list_of_all_dirs:
            redant.get_fattr(f"{self.mountpoint}/{direc}",
                             'trusted.glusterfs.pathinfo',
                             self.client_list[0])

        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        for direc in list_of_all_dirs:
            for brick in brick_list:
                host, brick_path = brick.split(':')
                redant.get_fattr(f"{brick_path}/{direc}",
                                 'trusted.glusterfs.pathinfo',
                                 host)

        # Clear mountpoint for next case
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_create_link_for_directory
        """
        Steps:
        - Create a directory on mountpoint
        - Create nested directories within the previous directory
        - Validate LAYOUT_IS_COMPLETE
        - Create symbolic links
        - Stat the files created for symbolic links
        - Get the inodes of the files
        - List the directories and files
        - Get the pathinfo of the directories
        - Do a readlink on the path, and validate
        """
        fqpath_for_test_dir = f"{self.mountpoint}/test_dir"
        redant.create_dir(self.mountpoint, "test_dir", self.client_list[0])

        redant.create_dir(self.mountpoint, "test_dir/dir{1..3}",
                          self.client_list[0])

        flag = redant.validate_files_in_dir(self.client_list[0],
                                            fqpath_for_test_dir,
                                            test_type=TEST_LAYOUT_IS_COMPLETE)
        if not flag:
            raise Exception("Layout of test directory is not complete")

        sym_link_path = f"{self.mountpoint}/test_sym_link"
        cmd = f"ln -s {fqpath_for_test_dir} {sym_link_path}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f'stat {sym_link_path}'
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])

        if 'symbolic link' not in ret['msg']:
            raise Exception("The type of the link is not symbolic")

        if not search(fqpath_for_test_dir, ret['msg']):
            raise Exception("sym link does not point to correct "
                            "location")

        cmd = f'ls -id {fqpath_for_test_dir} {sym_link_path}'
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])

        list_of_inode_numbers = "".join(ret['msg']).split('\n')
        if (list_of_inode_numbers[0].split(' ')[0]
           == list_of_inode_numbers[1].split(' ')[0]):
            raise Exception("The inode numbers of the dir and sym link "
                            "are same")

        cmd = f'ls {sym_link_path}'
        ret1 = redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = f'ls {fqpath_for_test_dir}'
        ret2 = redant.execute_abstract_op_node(cmd, self.client_list[0])

        if ret1['msg'] != ret2['msg']:
            raise Exception("The contents listed using the sym link "
                            "are not the same")

        cmd = f'getfattr -d -m . -e hex {sym_link_path}'
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])

        list_xattrs = ['trusted.gfid', 'trusted.glusterfs.dht']
        for xattr in list_xattrs:
            if xattr in ret['msg']:
                raise Exception("Important xattrs are being compromised"
                                " using the symlink at the mount point")

        path_info_1 = redant.get_pathinfo(fqpath_for_test_dir,
                                          self.client_list[0])
        path_info_2 = redant.get_pathinfo(sym_link_path,
                                          self.client_list[0])
        if path_info_1 != path_info_2:
            raise Exception("Pathinfos for test_dir and its sym link "
                            "are not same")

        cmd = f'readlink {sym_link_path}'
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])

        if ret['msg'][0].rstrip() != fqpath_for_test_dir:
            raise Exception("readlink did not return the path of the "
                            "test_dir")
