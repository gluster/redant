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

Description : check creation of different types of files.
"""

# disruptive;dist-disp,dist-arb,dist-rep,dist
from socket import gethostbyname
from tests.d_parent_test import DParentTest


class TestFileCreation(DParentTest):
    def _create_file_using_touch(self, file_name):
        """Creates a regular empty file"""
        cmd = f"touch {self.mountpoint}/{file_name}"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _check_file_stat_on_mountpoint(self, file_name, file_type):
        """Check the file-type on mountpoint"""
        file_stat = (self.redant.get_file_stat(self.client_list[0],
                     f"{self.mountpoint}/{file_name}"))
        if file_stat['msg']['fileType'] != file_type:
            raise Exception(f"File is not a {file_type}")

    def _file_exists(self, node, path):
        """Check if file exists at path on host
        """
        cmd = f"ls -ld {path}"
        ret = self.redant.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            return False
        return True

    def _is_file_present_on_brick(self, file_name):
        """Check if file is created on the backend-bricks as per
        the value of trusted.glusterfs.pathinfo xattr"""
        brick_list = (self.
                      redant.get_pathinfo(f"{self.mountpoint}/{file_name}",
                                          self.client_list[0]))

        for brick in brick_list['brickdir_paths']:
            host, path = brick.split(':')
            host = gethostbyname(host)
            ret = self._file_exists(host, path)
            if not ret:
                raise Exception(f"File {file_name} is not present on {brick}")

    def _compare_file_permissions(self, file_name,
                                  file_info_mnt=None, file_info_brick=None):
        """Check if the file's permission are same on mountpoint and
        backend-bricks"""
        if (file_info_mnt is None and file_info_brick is None):
            file_info_mnt = (self.redant.get_file_stat(self.client_list[0],
                             f"{self.mountpoint}/{file_name}"))
            file_info_mnt = file_info_mnt['msg']['permission']
            brick_list = (self.
                          redant.get_pathinfo(f"{self.mountpoint}/{file_name}",
                                              self.client_list[0]))
            file_info_brick = []
            for brick in brick_list['brickdir_paths']:
                host, path = brick.split(':')
                info_brick = self.redant.get_file_stat(host, path)
                file_info_brick.append(info_brick['msg']['permission'])

        for info in file_info_brick:
            if info != file_info_mnt:
                raise Exception(f"File details for {file_name} are diffrent"
                                " on backend-brick")

    def _check_change_time_mnt(self, file_name):
        """Find out the modification time for file on mountpoint"""
        file_ctime_mnt = (self.redant.get_file_stat(self.client_list[0],
                          f"{self.mountpoint}/{file_name}"))
        return file_ctime_mnt['msg']['st_ctime']

    def _check_change_time_brick(self, file_name):
        """Find out the modification time for file on backend-bricks"""
        brick_list = (self.
                      redant.get_pathinfo(f"{self.mountpoint}/{file_name}",
                                          self.client_list[0]))
        brick_mtime = []
        for brick in brick_list['brickdir_paths']:
            host, path = brick.split(':')
            cmd = f"ls -lR {path}"
            self.redant.execute_abstract_op_node(cmd, host)
            file_ctime_brick = self.redant.get_file_stat(host, path)
            brick_mtime.append(file_ctime_brick['msg']['st_ctime'])
        return brick_mtime

    def _collect_and_compare_file_info_on_mnt(
            self, link_file_name, values, expected=True):
        """Collect the files's permissions on mountpoint and compare"""
        stat_test_file = (self.redant.get_file_stat(self.client_list[0],
                          f"{self.mountpoint}/test_file"))
        stat_link_file = (self.redant.get_file_stat(self.client_list[0],
                          f"{self.mountpoint}/{link_file_name}"))

        for key in values:
            if expected is True:
                if stat_test_file['msg'][key] != stat_link_file['msg'][key]:
                    raise Exception(f"The {key} is not same for test_file"
                                    f" and {link_file_name}")
            else:
                if stat_test_file['msg'][key] == stat_link_file['msg'][key]:
                    raise Exception(f"Unexpected : The {key} is same for "
                                    f"test_file and {link_file_name}")

    def _compare_file_md5sum_on_mnt(self, link_file_name):
        """Collect and compare the md5sum for file on mountpoint"""
        md5sum_test_file = (self.redant.get_md5sum(self.client_list[0],
                            f"{self.mountpoint}/test_file"))
        if md5sum_test_file is None:
            raise Exception('Failed to get md5sum of original file')

        md5sum_link_file = (self.redant.get_md5sum(self.client_list[0],
                            f"{self.mountpoint}/{link_file_name}"))
        if md5sum_link_file is None:
            raise Exception('Failed to get md5sum of link file')

        if md5sum_test_file.split()[0] != md5sum_link_file.split()[0]:
            raise Exception(f"The md5sum for test_file and {link_file_name}"
                            " is not same")

    def _compare_file_md5sum_on_bricks(self, link_file_name):
        """Collect and compare md5sum for file on backend-bricks"""
        brick_list_test_file = (self.redant.get_pathinfo(
                                f"{self.mountpoint}/test_file",
                                self.client_list[0]))
        md5sum_list_test_file = []
        for brick in brick_list_test_file['brickdir_paths']:
            host, path = brick.split(':')
            md5sum_test_file = self.redant.get_md5sum(host, path).split()[0]
            md5sum_list_test_file.append(md5sum_test_file)

        brick_list_link_file = (self.redant.get_pathinfo(
                                f"{self.mountpoint}/{link_file_name}",
                                self.client_list[0]))
        md5sum_list_link_file = []
        for brick in brick_list_link_file['brickdir_paths']:
            host, path = brick.split(':')
            md5sum_link_file = self.redant.get_md5sum(host, path).split()[0]
            md5sum_list_link_file.append(md5sum_link_file)

            if md5sum_test_file != md5sum_link_file:
                raise Exception("The md5sum for test_file and "
                                f"{link_file_name} is not same on brick "
                                f"{brick}")

    def _compare_gfid_xattr_on_files(self, link_file_name, expected=True):
        """Collect and compare the value of trusted.gfid xattr for file
        on backend-bricks"""
        brick_list_test_file = (self.redant.get_pathinfo(
                                f"{self.mountpoint}/test_file",
                                self.client_list[0]))
        xattr_list_test_file = []
        for brick in brick_list_test_file['brickdir_paths']:
            host, path = brick.split(':')
            xattr_test_file = self.redant.get_fattr(path, "trusted.gfid", host)
            xattr_test_file = xattr_test_file[1].split('=')[1].strip()
            xattr_list_test_file.append(xattr_test_file[1:-1])

        brick_list_link_file = (self.redant.get_pathinfo(
                                f"{self.mountpoint}/{link_file_name}",
                                self.client_list[0]))
        xattr_list_link_file = []
        for brick in brick_list_link_file['brickdir_paths']:
            host, path = brick.split(':')
            xattr_link_file = self.redant.get_fattr(path, "trusted.gfid", host)
            xattr_link_file = xattr_link_file[1].split('=')[1].strip()
            xattr_list_link_file.append(xattr_link_file[1:-1])

        if expected is True:
            if xattr_list_test_file != xattr_list_link_file:
                raise Exception("Unexpected: The xattr trusted.gfid is not "
                                f"same for test_file and {link_file_name}")
        else:
            if xattr_list_test_file == xattr_list_link_file:
                raise Exception("Unexpected: The xattr trusted.gfid is "
                                f"same for test_file and {link_file_name}")

    def run_test(self, redant):
        """
        Steps:
        1) From mount point, Create a regular file
        eg:
        touch f1
        - From mount point, create character, block device and pipe files
        mknod c
        mknod b
        mkfifo
        2) Stat on the files created in Step-2 from mount point
        3) Verify that file is stored on only one bricks which is mentioned in
           trusted.glusterfs.pathinfo xattr
           On mount point -
           " getfattr -n trusted.glusterfs.pathinfo
           On all bricks
           " ls / "
        4) Verify that file permissions are same on mount point and sub-volumes
           " stat "
        5) Append some data to the file.
        6) List content of file to verify that data has been appended.
           " cat "
        7) Verify that file change time and size has been updated
           accordingly(from mount point and sub-volume)
           " stat / "
        """
        # Create a regular file
        self._create_file_using_touch("regfile")

        # Create a character and block file
        for (file_name, parameter) in [("blockfile", "b"), ("charfile", "c")]:
            cmd = f"mknod {self.mountpoint}/{file_name} {parameter} 1 5"
            redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create a pipe file
        cmd = f"mkfifo {self.mountpoint}/pipefile"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Stat all the files created on mount-point
        for (file_name, check_string) in [
                ("regfile", "regular empty file"),
                ("charfile", "character special file"),
                ("blockfile", "block special file"),
                ("pipefile", "fifo")]:
            self._check_file_stat_on_mountpoint(file_name, check_string)

        # Verify files are stored on backend bricks as per
        # the trusted.glusterfs.pathinfo
        file_types = ["regfile", "charfile", "blockfile", "pipefile"]

        for file_name in file_types:
            self._is_file_present_on_brick(file_name)

        # Verify that the file permissions are same on
        # mount-point and bricks
        for file_name in file_types:
            self._compare_file_permissions(file_name)

        # Note the modification time on mount and bricks
        # for all files. Also it should be same on mnt and bricks
        reg_mnt_ctime_1 = self._check_change_time_mnt("regfile")
        char_mnt_ctime_1 = self._check_change_time_mnt("charfile")
        block_mnt_ctime_1 = self._check_change_time_mnt("blockfile")
        fifo_mnt_ctime_1 = self._check_change_time_mnt("pipefile")

        reg_brick_ctime_1 = self._check_change_time_brick("regfile")
        char_brick_ctime_1 = self._check_change_time_brick("charfile")
        block_brick_ctime_1 = self._check_change_time_brick("blockfile")
        fifo_brick_ctime_1 = self._check_change_time_brick("pipefile")

        for (file_name, mnt_ctime, brick_ctime) in [
                ("regfile", reg_mnt_ctime_1, reg_brick_ctime_1),
                ("charfile", char_mnt_ctime_1, char_brick_ctime_1),
                ("blockfile", block_mnt_ctime_1, block_brick_ctime_1),
                ("pipefile", fifo_mnt_ctime_1, fifo_brick_ctime_1)]:
            self._compare_file_permissions(
                file_name, mnt_ctime, brick_ctime)

        # Append some data to the files
        for (file_name, data_str) in [
                ("regfile", "regular"),
                ("charfile", "character special"),
                ("blockfile", "block special")]:
            ret = (redant.append_string_to_file(
                   self.client_list[0], f"{self.mountpoint}/{file_name}",
                   f"Welcome! This is a {data_str} file"))
            if not ret:
                raise Exception("Failed to append data to {file_name}")

        # Check if the data has been appended
        check = "Welcome! This is a regular file"
        cmd = f"cat {self.mountpoint}/regfile"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        out = ret['msg'][0]
        if check not in out:
            raise Exception("No data present at regfile")

        # Append data to pipefile and check if it has been appended
        check = 'Hello'
        cmd = f"echo 'Hello' > {self.mountpoint}/pipefile"
        redant.execute_command_async(cmd, self.client_list[0])
        cmd = f"cat < {self.mountpoint}/pipefile"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        out = ret['msg'][0]
        if check not in out:
            raise Exception("Hello not recieved on the second terimnal")

        # Lookup on mount-point
        cmd = f"ls -lR {self.mountpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Collect ctime on mount point after appending data
        reg_mnt_ctime_2 = self._check_change_time_mnt("regfile")

        # After appending data the ctime for file should change
        if reg_mnt_ctime_1 == reg_mnt_ctime_2:
            raise Exception("Unexpected: The ctime has not been changed")

        # Collect the ctime on bricks
        reg_brick_ctime_2 = self._check_change_time_brick("regfile")

        # Check if the ctime has changed on bricks as per mount
        self._compare_file_permissions(
            "regfile", reg_mnt_ctime_2, reg_brick_ctime_2)

        """
        Description: link file create, validate and access file
                     using it

        Steps:
        1) From mount point, create a regular file
        2) Verify that file is stored on only on bricks which is
           mentioned in trusted.glusterfs.pathinfo xattr
        3) From mount point create hard-link file for the created file
        4) From mount point stat on the hard-link file and original file;
           file inode, permission, size should be same
        5) From mount point, verify that file contents are same
           "md5sum"
        6) Verify "trusted.gfid" extended attribute of the file
           on sub-vol
        7) From sub-volume stat on the hard-link file and original file;
           file inode, permission, size should be same
        8) From sub-volume verify that content of file are same
        """
        # Create a regular file
        self._create_file_using_touch("test_file")

        # Check file is create on bricks as per trusted.glusterfs.pathinfo
        self._is_file_present_on_brick("test_file")

        # Create a hard-link file for the test_file
        ret = (redant.create_link_file(
               self.client_list[0], f"{self.mountpoint}/test_file",
               f"{self.mountpoint}/hardlink_file"))
        if not ret:
            raise Exception("Unable to create hard link for test_file")

        # On mountpoint perform stat on original and hard-link file
        values = ["inode", "permission", "st_size"]
        (self._collect_and_compare_file_info_on_mnt(
         "hardlink_file", values, expected=True))

        # Check the md5sum on original and hard-link file on mountpoint
        self._compare_file_md5sum_on_mnt("hardlink_file")

        # Compare the value of trusted.gfid for test_file and hard-link file
        # on backend-bricks
        self._compare_gfid_xattr_on_files("hardlink_file")

        # On backend bricks perform stat on original and hard-link file
        values = ["inode", "permission", "st_size"]
        self._collect_and_compare_file_info_on_mnt("hardlink_file", values)

        # On backend bricks check the md5sum
        self._compare_file_md5sum_on_bricks("hardlink_file")

        # Clear mountpoint before next test
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        """
        Description: Create symbolic link file, validate and access file
                     using it

        Steps:
        1) From mount point, create a regular file
        2) Verify that file is stored on only on bricks which is
           mentioned in trusted.glusterfs.pathinfo xattr
        3) From mount point create symbolic link file for the created file
        4) From mount point stat on the symbolic link file and original file;
           file inode should be different
        5) From mount point, verify that file contents are same
           "md5sum"
        6) Verify "trusted.gfid" extended attribute of the file
           on sub-vol
        7) Verify readlink on symbolic link from mount point
           "readlink "
        8) From sub-volume verify that content of file are same
        """
        # Create a regular file on mountpoint
        self._create_file_using_touch("test_file")

        # Check file is create on bricks as per trusted.glusterfs.pathinfo
        self._is_file_present_on_brick("test_file")

        # Create a symbolic-link file for the test_file
        ret = (redant.create_link_file(
               self.client_list[0], f"{self.mountpoint}/test_file",
               f"{self.mountpoint}/softlink_file", True))
        if not ret:
            raise Exception("Unable to create soft link for test_file")

        # On mountpoint perform stat on original and symbolic-link file
        # The value of inode should be different
        values = ["inode"]
        self._collect_and_compare_file_info_on_mnt("softlink_file", values)

        # Check the md5sum on original and symbolic-link file on mountpoint
        self._compare_file_md5sum_on_mnt("softlink_file")

        # Compare the value of trusted.gfid for test_file and
        # symbolic-link file on backend-bricks
        self._compare_gfid_xattr_on_files("softlink_file")

        # Verify readlink on symbolic-link from mount point
        cmd = f"readlink {self.mountpoint}/softlink_file"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        out = ret['msg'][0].strip()
        if out == f"{self.mountpoint}test_file":
            raise Exception("Symbolic link points to incorrect file")

        # Check the md5sum on original and symbolic-link file on backend bricks
        self._compare_file_md5sum_on_bricks("softlink_file")
