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
    Test cases in this module tests DHT Rename directory
"""

# disruptive;dist,rep,arb,disp,dist-rep,dist-disp,dist-arb
from common.ops.gluster_ops.constants import \
    (FILETYPE_DIRS, TEST_LAYOUT_IS_COMPLETE,
     TEST_FILE_EXISTS_ON_HASHED_BRICKS)
from tests.d_parent_test import DParentTest


class TestDHTRenameDirectory(DParentTest):

    def _create_files(self, host, root, files, content):
        """
        This method is responsible to create file structure by given
        sequence with the same content for all of the files
        """
        for item in files:
            dir_name = root
            file_name = item
            if item.find('/') != -1:
                folders_tree = "/".join(item.split('/')[:-1])
                file_name = item[-1]
                dir_name = f'{root}/{folders_tree}'
                cmd = f"mkdir -p {dir_name}"
                self.redant.execute_abstract_op_node(cmd, host)
            cmd = f'echo "{content}" > {dir_name}/{file_name}'
            ret = self.redant.execute_abstract_op_node(cmd, host, False)
            if ret['error_code'] != 0:
                self.redant.logger.error("Error on file creation")
                return False
        return True

    def run_test(self, redant):
        """
        Case 1: Test rename directory with no destination folder
        Steps:
        - Create and start a volume
        - Mount it on client
        - Validate LAYOUT
        - Create source folder on mountpoint
        - Create files and directories under the source folder
        - Validate files on HASHED_BRICKS
        - Check if destination dir exists
        - Rename source folder to destination dir
        - Vaildate the presence of src and dst dirs on bricks
        """
        self.files = (
            'a.txt',
            'b.txt',
            'sub_folder/c.txt',
            'sub_folder/d.txt'
        )
        dirs = {
            'initial': '{root}/folder_{client_index}',
            'new_folder': '{root}/folder_renamed{client_index}'
        }
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for mount_index, mount_obj in enumerate(self.mounts):
            client_host = mount_obj['client']
            mountpoint = mount_obj['mountpath']

            initial_folder = dirs['initial'].format(
                root=mountpoint,
                client_index=mount_index
            )

            ret = (redant.validate_files_in_dir(client_host, mountpoint,
                   test_type=TEST_LAYOUT_IS_COMPLETE,
                   file_type=FILETYPE_DIRS))
            if not ret:
                raise Exception("Expected - Layout is complete")

            # Create source folder on mount point
            cmd = f"mkdir -p {initial_folder}"
            redant.execute_abstract_op_node(cmd, client_host)

            # Create files and directories
            ret = self._create_files(client_host, initial_folder, self.files,
                                     content='Textual content')
            if not ret:
                raise Exception('Unable to create files on mount point')

            ret = (redant.validate_files_in_dir(client_host, mountpoint,
                   test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS))
            if not ret:
                raise Exception("Expected - Files and dirs are stored "
                                "on hashed bricks")

            new_folder_name = dirs['new_folder'].format(
                root=mountpoint,
                client_index=mount_index
            )
            # Check if destination dir does not exist
            if redant.path_exists(client_host, new_folder_name):
                raise Exception('Expected New folder name should not exists')

            # Rename source folder
            ret = redant.move_file(client_host, initial_folder,
                                   new_folder_name)
            if not ret:
                raise Exception("Rename direcoty failed")

            # Old dir does not exists and destination is present
            if redant.path_exists(client_host, initial_folder):
                raise Exception('Old dir should not exists')

            if not redant.path_exists(client_host, new_folder_name):
                raise Exception('Destination dir does not exists')

            # Check bricks for source and destination directories
            brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
            for brick_item in brick_list:
                brick_host, brick_dir = brick_item.split(':')
                initial_folder = dirs['initial'].format(
                    root=brick_dir,
                    client_index=mount_index
                )
                new_folder_name = dirs['new_folder'].format(
                    root=brick_dir,
                    client_index=mount_index
                )

                if redant.path_exists(brick_host, initial_folder):
                    raise Exception('Old dir should not exists')

                if not redant.path_exists(brick_host, new_folder_name):
                    raise Exception('Destination dir does not exists')

        # Clear the mountpoint for next case
        for mount_obj in self.mounts:
            cmd = f"rm -rf {mount_obj['mountpath']}/*"
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

        # Case 2: test_rename_directory_with_dest_folder
        """
        Steps:
        - Create and start a volume
        - Mount it on client
        - Validate LAYOUT
        - Create source folder on mountpoint
        - Create dest dir on mountpoint
        - Create files and directories under the source folder
        - Validate files on HASHED_BRICKS
        - Check if destination dir exists
        - Rename source folder to destination dir
        - Vaildate the presence of src and dst dirs on bricks
        """
        dirs = {
            'initial_folder': '{root}/folder_{client_index}/',
            'new_folder': '{root}/new_folder_{client_index}/'
        }

        for mount_index, mount_obj in enumerate(self.mounts):
            client_host = mount_obj['client']
            mountpoint = mount_obj['mountpath']

            initial_folder = dirs['initial_folder'].format(
                root=mountpoint,
                client_index=mount_index
            )

            ret = (redant.validate_files_in_dir(client_host, mountpoint,
                   test_type=TEST_LAYOUT_IS_COMPLETE,
                   file_type=FILETYPE_DIRS))
            if not ret:
                raise Exception("Expected - Layout is complete")

            # Create a folder on mount point
            cmd = f"mkdir -p {initial_folder}"
            redant.execute_abstract_op_node(cmd, client_host)

            new_folder_name = dirs['new_folder'].format(
                root=mountpoint,
                client_index=mount_index
            )
            # Create destination directory
            cmd = f"mkdir -p {new_folder_name}"
            redant.execute_abstract_op_node(cmd, client_host)

            # Create files and directories
            ret = self._create_files(client_host, initial_folder, self.files,
                                     content='Textual content')
            if not ret:
                raise Exception('Unable to create files on mount point')

            ret = (redant.validate_files_in_dir(client_host, mountpoint,
                   test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS))
            if not ret:
                raise Exception("Expected - Files and dirs are stored "
                                "on hashed bricks")

            # Rename source folder to destination
            ret = redant.move_file(client_host, initial_folder,
                                   new_folder_name)
            if not ret:
                raise Exception("Rename direcoty failed")

            # Old dir does not exists and destination is present
            if redant.path_exists(client_host, initial_folder):
                raise Exception('Old dir should not exists')

            if not redant.path_exists(client_host, new_folder_name):
                raise Exception('Destination dir does not exists')

            # Check bricks for source and destination directories
            brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
            for brick_item in brick_list:
                brick_host, brick_dir = brick_item.split(':')

                initial_folder = dirs['initial_folder'].format(
                    root=brick_dir,
                    client_index=mount_index
                )
                new_folder_name = dirs['new_folder'].format(
                    root=brick_dir,
                    client_index=mount_index
                )

                if redant.path_exists(brick_host, initial_folder):
                    raise Exception('Old dir should not exists')

                if not redant.path_exists(brick_host, new_folder_name):
                    raise Exception('Destination dir does not exists')
