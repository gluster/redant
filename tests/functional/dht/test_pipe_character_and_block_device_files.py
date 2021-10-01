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

 Description:
    TC to check pipe character and block device files
"""

# disruptive;dist,dist-rep,dist-arb
from socket import gethostbyname
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestPipeCharacterAndBlockDeviceFiles(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 5

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _create_character_and_block_device_files(self):
        """Create character and block device files"""
        self.list_of_device_files, self.file_names = [], []
        for ftype, filename in (('b', 'blockfile'), ('c', 'Characterfile')):

            # Create files using mknod
            cmd = f"cd {self.mountpoint}; mknod {filename} {ftype} 1 5"
            self.redant.execute_abstract_op_node(cmd, self.client_list[0])

            # Add file names and file path to lists
            self.file_names.append(filename)
            self.list_of_device_files.append(f'{self.mountpoint}/{filename}')

        # Create file type list for the I/O
        self.filetype_list = ["block special file", "character special file"]

    def _create_pipe_file(self):
        """Create pipe files"""

        # Create pipe files using mkfifo
        cmd = f"cd {self.mountpoint}; mkfifo fifo"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Populate variables with fifo file details
        self.list_of_device_files = [f'{self.mountpoint}/fifo']
        self.file_names = ['fifo']
        self.filetype_list = ['fifo']

    def _set_xattr_trusted_foo(self, xattr_val):
        """Sets xattr trusted.foo on all the files"""
        for fname in self.list_of_device_files:
            self.redant.set_fattr(fname, 'trusted.foo',
                                  self.client_list[0], xattr_val)

    def _delete_xattr_trusted_foo(self):
        """Removes xattr trusted.foo from all the files."""
        for fname in self.list_of_device_files:
            self.redant.delete_fattr(fname, 'trusted.foo',
                                     self.client_list[0])

    def _check_custom_xattr_trusted_foo(self, xattr_val, visible=True):
        """Check custom xttar from mount point and on bricks."""
        # Check custom xattr from mount point
        for fname in self.list_of_device_files:
            ret = self.redant.get_fattr(fname, 'trusted.foo',
                                        self.client_list[0], encode='text',
                                        excep=False)
            if visible:
                val = ret['msg'][1].split('=')[1].strip()
                if val[1:-1] != xattr_val:
                    raise Exception("Custom xattr not found from mount.")
            else:
                if ret['error_code'] == 0 and \
                   "No such attribute" not in ret['error_msg']:
                    raise Exception("Custom attribute visible at mount "
                                    "point even after deletion")

        # Check custom xattr on bricks
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        for brick in bricks_list:
            node, brick_path = brick.split(':')
            files_on_bricks = self.redant.get_dir_contents(brick_path, node)
            files = [
                fname for fname in self.file_names
                if fname in files_on_bricks]
            for fname in files:
                ret = self.redant.get_fattr(f"{brick_path}/{fname}",
                                            'trusted.foo', node,
                                            encode='text', excep=False)
                if visible:
                    val = ret['msg'][1].split('=')[1].strip()
                    if val[1:-1] != xattr_val:
                        raise Exception("Custom xattr not visible on bricks.")
                else:
                    if ret['error_code'] == 0 and \
                       "No such attribute" not in ret['error_msg']:
                        raise Exception("Custom attribute visible on bricks "
                                        "even after deletion")

    def _check_if_files_are_stored_only_on_expected_bricks(self):
        """Check if files are stored only on expected bricks"""
        for fname in self.list_of_device_files:
            # Fetch trusted.glusterfs.pathinfo and check if file is present on
            # brick or not
            ret = self.redant.get_pathinfo(fname, self.client_list[0])
            if ret is None:
                raise Exception("Unable to get trusted.glusterfs.pathinfo "
                                f"of file {fname}")

            present_brick_list = []
            for brick_path in ret['brickdir_paths']:
                node, path = brick_path.split(":")
                ret = self.redant.path_exists(node, path)
                if not ret:
                    raise Exception(f"Unable to find file {fname} on brick "
                                    f"{path}")
                brick_text = brick_path.split('/')[:-1]
                if brick_text[0][0:2].isdigit():
                    brick_text[0] = f"{gethostbyname(brick_text[0][:-1])}:"
                present_brick_list.append('/'.join(brick_text))

            # Check on other bricks where file doesn't exist
            brick_list = self.redant.get_all_bricks(self.vol_name,
                                                    self.server_list[0])
            other_bricks = [
                brk for brk in brick_list if brk not in present_brick_list]
            for brick in other_bricks:
                node, path = brick.split(':')
                ret = (self.redant.path_exists(node,
                       f"{path}/{fname.split('/')[-1]}"))
                if ret:
                    raise Exception(f"Unexpected: Able to find file {fname}"
                                    f" on brick {path}")

    def _check_filetype_of_files_from_mountpoint(self):
        """Check filetype of files from mountpoint"""
        for filetype in self.filetype_list:
            # Check if filetype is as expected
            fl = self.list_of_device_files[self.filetype_list.index(filetype)]
            ret = self.redant.get_file_stat(self.client_list[0], fl)
            if ret['msg']['fileType'] != filetype:
                raise Exception("File type not reflecting properly for "
                                f"{filetype}")

    def _compare_stat_output_from_mount_point_and_bricks(self):
        """Compare stat output from mountpoint and bricks"""
        for fname in self.list_of_device_files:
            # Fetch stat output from mount point
            mountpoint_stat = self.redant.get_file_stat(self.client_list[0],
                                                        fname)
            bricks = self.redant.get_pathinfo(fname, self.client_list[0])

            # Fetch stat output from bricks
            for brick_path in bricks['brickdir_paths']:
                node, path = brick_path.split(":")
                brick_stat = self.redant.get_file_stat(node, path)
                for key in ("fileType", "permission", "st_size", "user",
                            "group", "st_uid", "st_gid", "st_atime",
                            "st_mtime", "st_ctime"):
                    if mountpoint_stat['msg'][key] != brick_stat['smg'][key]:
                        raise Exception("Difference observed between stat "
                                        "output of mountpoint and bricks for"
                                        f" file {fname}")

    def run_test(self, redant):
        """
        Case 1: test_character_and_block_device_file_creation
        Test case:
        1. Create distributed volume with 5 sub-volumes, start amd mount it.
        2. Create character and block device files.
        3. Check filetype of files from mount point.
        4. Verify that the files are stored on only the bricks which is
           mentioned in trusted.glusterfs.pathinfo xattr.
        5. Verify stat output from mount point and bricks.
        """
        self.list_of_device_files = []
        self.file_names = []

        # Create Character and block device files
        self._create_character_and_block_device_files()

        # Check filetype of files from mount point
        self._check_filetype_of_files_from_mountpoint()

        # Verify that the files are stored on only the bricks which is
        # mentioned in trusted.glusterfs.pathinfo xattr
        self._check_if_files_are_stored_only_on_expected_bricks()

        # Verify stat output from mount point and bricks
        self._compare_stat_output_from_mount_point_and_bricks()

        # Clear mountpoint
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_character_and_block_device_file_removal_using_rm
        """
        Test case:
        1. Create distributed volume with 5 sub-volumes, start and mount it.
        2. Create character and block device files.
        3. Check filetype of files from mount point.
        4. Verify that the files are stored on only one bricks which is
           mentioned in trusted.glusterfs.pathinfo xattr.
        5. Delete the files.
        6. Verify if the files are delete from all the bricks
        """
        # Create Character and block device files
        self._create_character_and_block_device_files()

        # Check filetype of files from mount point
        self._check_filetype_of_files_from_mountpoint()

        # Verify that the files are stored on only the bricks which is
        # mentioned in trusted.glusterfs.pathinfo xattr
        self._check_if_files_are_stored_only_on_expected_bricks()

        # Delete both the character and block device files
        for fname in self.list_of_device_files:
            cmd = f"rm -rf {fname}"
            redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Verify if the files are deleted from all bricks or not
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        for brick in brick_list:
            node, path = brick.split(':')
            for fname in self.file_names:
                ret = redant.path_exists(node, f"{path}/{fname}")
                if ret:
                    raise Exception("Unexpected: Able to find file {fname} "
                                    f"on brick {path} even after deleting")

        # Clear mountpoint
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 3: test_character_and_block_device_file_with_custom_xattrs
        """
        Test case:
        1. Create distributed volume with 5 sub-volumes, start and mount it.
        2. Create character and block device files.
        3. Check filetype of files from mount point.
        4. Set a custom xattr for files.
        5. Verify that xattr for files is displayed on mount point and bricks.
        6. Modify custom xattr value and verify that xattr for files
           is displayed on mount point and bricks.
        7. Remove the xattr and verify that custom xattr is not displayed.
        8. Verify that mount point and brick shows pathinfo xattr properly.
        """
        # Create Character and block device files
        self._create_character_and_block_device_files()

        # Check filetype of files from mount point
        self._check_filetype_of_files_from_mountpoint()

        # Set a custom xattr for files
        self._set_xattr_trusted_foo("bar1")

        # Verify that xattr for files is displayed on mount point and bricks
        self._check_custom_xattr_trusted_foo("bar1")

        # Modify custom xattr value
        self._set_xattr_trusted_foo("bar2")

        # Verify that xattr for files is displayed on mount point and bricks
        self._check_custom_xattr_trusted_foo("bar2")

        # Remove the xattr
        self._delete_xattr_trusted_foo()

        # Verify that custom xattr is not displayed
        self._check_custom_xattr_trusted_foo("bar2", visible=False)

        # Verify that mount point shows pathinfo xattr properly
        self._check_if_files_are_stored_only_on_expected_bricks()

        # Clear mountpoint
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 4: test_pipe_file_create
        """
        Test case:
        1. Create distributed volume with 5 sub-volumes, start and mount it.
        2. Create a pipe file.
        3. Check filetype of files from mount point.
        4. Verify that the files are stored on only the bricks which is
           mentioned in trusted.glusterfs.pathinfo xattr.
        5. Verify stat output from mount point and bricks.
        6. Write data to fifo file and read data from fifo file
           from the other instance of the same client.
        """
        # Create a pipe file
        self._create_pipe_file()

        # Check filetype of files from mount point
        self._check_filetype_of_files_from_mountpoint()

        # Verify that the files are stored on only the bricks which is
        # mentioned in trusted.glusterfs.pathinfo xattr
        self._check_if_files_are_stored_only_on_expected_bricks()

        # Verify stat output from mount point and bricks
        self._compare_stat_output_from_mount_point_and_bricks()

        # Write data to fifo file and read data from fifo file
        # from the other instance of the same client.
        cmd = f"echo 'Hello' > {self.list_of_device_files[0]}"
        redant.execute_command_async(cmd, self.client_list[0])

        cmd = f"cat < {self.list_of_device_files[0]}"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        if ret['msg'][0].strip() != "Hello":
            raise Exception("Hello not recieved on the second terimnal")
