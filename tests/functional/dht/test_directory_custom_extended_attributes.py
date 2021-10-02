"""
 Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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
    Test cases in this module tests custom extended attribute validation
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
from common.ops.gluster_ops.constants import \
    (FILETYPE_DIR, FILETYPE_LINK, TEST_FILE_EXISTS_ON_HASHED_BRICKS)
from tests.d_parent_test import DParentTest


class TestDirectoryCustomExtendedAttributes(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        - Create and start a volume
        - Mount the volume on clients
        - Create a dir on mountpoint
        - Validate hash layout
        - Verify that mountpoint should not display xattrs
        - Veirfy pathinfo xattr is present
        - Create a custom xattr
        - Verify that the custom xattr is present
        - Create a link file and repeat the same steps as above
        """
        dir_prefix = '{root}/folder_{client_index}'
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for mount_index, mount_obj in enumerate(self.mounts):
            folder_name = dir_prefix.format(
                root=mount_obj['mountpath'],
                client_index=mount_index
            )

            # Create a directory from mount point
            cmd = f"mkdir -p {folder_name}"
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            # Verify that hash layout values are set on each
            # bricks for the dir
            ret = (redant.validate_files_in_dir(
                   mount_obj['client'], mount_obj['mountpath'],
                   test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS,
                   file_type=FILETYPE_DIR))
            if not ret:
                raise Exception("Expected - Directory is stored "
                                "on hashed bricks")

            # Verify that mount point should not display
            # xattr : trusted.gfid and dht
            ret = redant.get_fattr_list(folder_name, mount_obj['client'])

            if 'trusted.gfid' in ret:
                raise Exception("Unexpected: Extended attribute trusted.gfid"
                                " is presented on mount point")

            if 'trusted.glusterfs.dht' in ret:
                raise Exception("Unexpected: Extended attribute "
                                "trusted.glusterfs.dht is present")

            # Verify that mount point shows pathinfo xattr
            redant.get_fattr(mount_obj['mountpath'],
                             'trusted.glusterfs.pathinfo',
                             mount_obj['client'], encode="text")

            # Create a custom xattr for dir
            redant.set_fattr(folder_name, 'user.foo',
                             mount_obj['client'], 'bar2')

            # Verify that custom xattr for directory is displayed
            # on mount point and bricks
            ret = redant.get_fattr(folder_name, 'user.foo',
                                   mount_obj['client'], encode="text")
            val = ret[1].split('=')[1].strip()[1:-1]
            if val != 'bar2':
                raise Exception("Xattr attribute user.foo is not present "
                                "on mount point")

            brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
            for brick in brick_list:
                brick_server, brick_dir = brick.split(':')
                brick_path = dir_prefix.format(root=brick_dir,
                                               client_index=mount_index)

                ret = redant.get_fattr(brick_path, 'user.foo', brick_server,
                                       encode="text")
                val = ret[1].split('=')[1].strip()[1:-1]
                if val != 'bar2':
                    raise Exception("Xattr attribute user.foo is not present"
                                    " on brick")

            # Delete custom attribute
            redant.delete_fattr(folder_name, 'user.foo', mount_obj['client'])

            # Verify that custom xattr is not displayed after delete
            # on mount point and on the bricks
            ret = redant.get_fattr(folder_name, 'user.foo',
                                   mount_obj['client'], encode="text",
                                   excep=False)
            if ret['error_code'] == 0:
                raise Exception("Xattr user.foo is present on mount point"
                                " even after deletion")

            brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
            for brick in brick_list:
                brick_server, brick_dir = brick.split(':')
                brick_path = dir_prefix.format(root=brick_dir,
                                               client_index=mount_index)

                ret = redant.get_fattr(brick_path, 'user.foo', brick_server,
                                       encode="text", excep=False)
                if ret['error_code'] == 0:
                    raise Exception("Xattr user.foo is present on brick"
                                    " even after deletion")

        # Repeat all of the steps for link of created directory
        for mount_index, mount_obj in enumerate(self.mounts):
            linked_folder_name = dir_prefix.format(
                root=mount_obj['mountpath'],
                client_index=f"{mount_index}_linked"
            )

            folder_name = dir_prefix.format(
                root=mount_obj['mountpath'],
                client_index=mount_index
            )
            # Create link to created dir
            command = f"ln -s {folder_name} {linked_folder_name}"
            redant.execute_abstract_op_node(command, mount_obj['client'])

            if not redant.path_exists(mount_obj['client'],
                                      linked_folder_name):
                raise Exception("Link does not exists")

            # Verify that hash layout values are set on each
            # bricks for the link to dir
            ret = (redant.validate_files_in_dir(
                   mount_obj['client'], mount_obj['mountpath'],
                   test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS,
                   file_type=FILETYPE_LINK))
            if not ret:
                raise Exception("Expected - Directory is stored "
                                "on hashed bricks")

            # Verify that mount point should not display xattr :
            # trusted.gfid and dht
            ret = redant.get_fattr_list(linked_folder_name,
                                        mount_obj['client'])

            if 'trusted.gfid' in ret:
                raise Exception("Unexpected: Extended attribute trusted.gfid"
                                " is presented on mount point")

            if 'trusted.glusterfs.dht' in ret:
                raise Exception("Unexpected: Extended attribute "
                                "trusted.glusterfs.dht is present")

            # Verify that mount point shows pathinfo xattr
            redant.get_fattr(mount_obj['mountpath'],
                             'trusted.glusterfs.pathinfo',
                             mount_obj['client'], encode="text")

            # Set custom Attribute to link
            redant.set_fattr(linked_folder_name, 'user.foo',
                             mount_obj['client'], 'bar2')

            # Verify that custom xattr for directory is displayed
            # on mount point and bricks
            ret = redant.get_fattr(linked_folder_name, 'user.foo',
                                   mount_obj['client'], encode="text")
            val = ret[1].split('=')[1].strip()[1:-1]
            if val != 'bar2':
                raise Exception("Xattr attribute user.foo is not present "
                                "on mount point")

            brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
            for brick in brick_list:
                brick_server, brick_dir = brick.split(':')
                brick_path = (dir_prefix.format(root=brick_dir,
                              client_index=f"{mount_index}_linked"))
                cmd = f"[ -f {brick_path} ] && echo 'yes' || 'no'"
                ret = redant.execute_abstract_op_node(cmd, brick_server)
                if "no" in ret['msg'][0].strip():
                    redant.logger.info("Link does not exists")
                    continue

                ret = redant.get_fattr(brick_path, 'user.foo', brick_server,
                                       encode="text")
                val = ret[1].split('=')[1].strip()[1:-1]
                if val != 'bar2':
                    raise Exception("Xattr attribute user.foo is not present"
                                    " on brick")

            # Delete custom attribute
            redant.delete_fattr(linked_folder_name, 'user.foo',
                                mount_obj['client'])

            # Verify that custom xattr is not displayed after delete
            # on mount point and on the bricks
            ret = redant.get_fattr(linked_folder_name, 'user.foo',
                                   mount_obj['client'], encode="text",
                                   excep=False)
            if ret['error_code'] == 0:
                raise Exception("Xattr user.foo is present on mount point"
                                " even after deletion")

            brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
            for brick in brick_list:
                brick_server, brick_dir = brick.split(':')
                brick_path = (dir_prefix.format(root=brick_dir,
                              client_index=f"{mount_index}_linked"))
                cmd = f"[ -f {brick_path} ] && echo 'yes' || 'no'"
                ret = redant.execute_abstract_op_node(cmd, brick_server)
                if "no" in ret['msg'][0].strip():
                    redant.logger.info("Link does not exists")
                    continue

                ret = redant.get_fattr(brick_path, 'user.foo', brick_server,
                                       encode="text", excep=False)
                if ret['error_code'] == 0:
                    raise Exception("Xattr user.foo is present on brick"
                                    " even after deletion")
