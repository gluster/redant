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
    TC to check custom xattr on mountpoint and bricks
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
from common.ops.gluster_ops.constants import \
    (FILETYPE_FILES, TEST_FILE_EXISTS_ON_HASHED_BRICKS)
from tests.d_parent_test import DParentTest


class TestDhtCustomXattrClass(DParentTest):

    def _check_custom_xattr_visible(self, xattr_val):
        """
        Check custom xttar from mount point and on bricks.
        """
        # Check custom xattr from mount point
        for mount_object in self.mounts:
            for fname in self.files_and_soft_links:
                ret = self.redant.get_fattr(fname, 'user.foo',
                                            mount_object['client'],
                                            encode='text')
                attr_val = ret[1].split('=')[1].strip()
                if attr_val[1:-1] != xattr_val:
                    raise Exception("Custom xattr not found from mount.")

        # Check custom xattr on bricks
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        for brick in bricks_list:
            node, brick_path = brick.split(':')
            files_on_bricks = self.redant.get_dir_contents(brick_path, node)
            files = []
            for fname in self.list_of_files:
                if fname.split('/')[3] in files_on_bricks:
                    files.append(fname.split('/')[3])

            for fname in files:
                ret = self.redant.get_fattr(f"{brick_path}/{fname}",
                                            'user.foo', node,
                                            encode='text')
                attr_val = ret[1].split('=')[1].strip()
                if attr_val[1:-1] != xattr_val:
                    raise Exception("Custom xattr not found from bricks.")

    def _delete_xattr_user_foo(self, list_of_files):
        """
        Removes xattr user.foo from all the files.
        """
        for fname in list_of_files:
            self.redant.delete_fattr(fname, 'user.foo', self.client_list[0])

    def _set_xattr_user_foo(self, list_of_files, xattr_val):
        """
        sets xattr user.foo on all the files.
        """
        for fname in list_of_files:
            self.redant.set_fattr(fname, 'user.foo', self.client_list[0],
                                  xattr_val)

    def _check_for_trusted_glusterfs_pathinfo(self, list_of_files):
        """
        Check if trusted.glusterfs.pathinfo is visible.
        """
        for fname in list_of_files:
            ret = self.redant.get_fattr(fname, 'trusted.glusterfs.pathinfo',
                                        self.client_list[0])
            attr_val = ret[1].split('=')[1].strip()
            if attr_val is None:
                raise Exception("Pathinfo xattr not visible on mountpoint")

    def _check_mount_point_and_bricks_for_xattr(self, list_of_all_files):
        """
        Check xattr on mount point and bricks.
        """
        # Check if xattr is visable from mount point
        for mount_object in self.mounts:
            for fname in list_of_all_files:
                ret = self.redant.get_fattr(fname, 'user.foo',
                                            mount_object['client'],
                                            encode='text', excep=False)
                if ret['error_code'] == 0 and \
                   'No such attribute' not in ret['error_msg']:
                    raise Exception("Custom xattr visible on mountpoint")

        # Check if xattr is visable from bricks
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        for brick in bricks_list:
            node, brick_path = brick.split(':')
            files_on_bricks = self.redant.get_dir_contents(brick_path, node)
            files = []
            for fname in self.list_of_files:
                if fname.split('/')[3] in files_on_bricks:
                    files.append(fname.split('/')[3])

            for fname in files:
                ret = self.redant.get_fattr(f"{brick_path}/{fname}",
                                            'user.foo', node,
                                            encode='text', excep=False)
                if ret['error_code'] == 0 and \
                   'No such attribute' not in ret['error_msg']:
                    raise Exception("Custom xattr still visible on bricks")

    def run_test(self, redant):
        """
        Test case:
        1.Create a gluster volume and start it.
        2.Create file and link files.
        3.Create a custom xattr for file.
        4.Verify that xattr for file is displayed on
          mount point and bricks
        5.Modify custom xattr value and verify that xattr
          for file is displayed on mount point and bricks
        6.Verify that custom xattr is not displayed
          once you remove it
        7.Create a custom xattr for symbolic link.
        8.Verify that xattr for symbolic link
          is displayed on mount point and sub-volume
        9.Modify custom xattr value and verify that
          xattr for symbolic link is displayed on
          mount point and bricks
        10.Verify that custom xattr is not
           displayed once you remove it.
        """
        # Initializing variables
        self.list_of_files = []
        list_of_hardlinks, list_of_softlinks = [], []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for number in range(1, 3):
            # Create regular files
            fname = f'{self.mountpoint}/regular_file_{number}'
            ret = redant.append_string_to_file(self.client_list[0], fname,
                                               'Sample content for file.')
            if not ret:
                raise Exception("Unable to create regular file "
                                f"{fname}")
            self.list_of_files.append(fname)

            # Create hard link for file
            hardlink = f'{self.mountpoint}/link_file_{number}'
            ret = redant.create_link_file(self.client_list[0], fname,
                                          hardlink)
            if not ret:
                raise Exception("Unable to create hard link file "
                                f"{hardlink}")
            list_of_hardlinks.append(hardlink)

            # Create soft link for file
            softlink = f'{self.mountpoint}/symlink_file_{number}'
            ret = redant.create_link_file(self.client_list[0], fname,
                                          softlink, True)
            if not ret:
                raise Exception("Unable to create symlink file "
                                f"{softlink}")
            list_of_softlinks.append(softlink)

        self.files_and_soft_links = self.list_of_files + list_of_softlinks

        # Check if files are created on the right subvol
        ret = (redant.validate_files_in_dir(self.client_list[0],
               self.mount_point, file_type=FILETYPE_FILES,
               test_type=TEST_FILE_EXISTS_ON_HASHED_BRICKS))
        if not ret:
            raise Exception("Files not created on correct sub-vols")

        # Set custom xattr on all the regular files
        self._set_xattr_user_foo(self.list_of_files, 'bar2')

        # Check if custom xattr is set to all the regular files
        self._check_custom_xattr_visible("bar2")

        # Change the custom xattr on all the regular files
        self._set_xattr_user_foo(self.list_of_files, 'ABC')

        # Check if xattr is set to all the regular files
        self._check_custom_xattr_visible("ABC")

        # Delete Custom xattr from all regular files
        self._delete_xattr_user_foo(self.list_of_files)

        # Check mount point and brick for the xattr
        list_of_all_files = list_of_hardlinks + self.files_and_soft_links
        self._check_mount_point_and_bricks_for_xattr(list_of_all_files)

        # Check if pathinfo xattr is visible
        self._check_for_trusted_glusterfs_pathinfo(self.list_of_files)

        # Set custom xattr on all the regular files
        self._set_xattr_user_foo(list_of_softlinks, 'bar2')

        # Check if custom xattr is set to all the regular files
        self._check_custom_xattr_visible("bar2")

        # Change the custom xattr on all the regular files
        self._set_xattr_user_foo(list_of_softlinks, 'ABC')

        # Check if xattr is set to all the regular files
        self._check_custom_xattr_visible("ABC")

        # Delete Custom xattr from all regular files
        self._delete_xattr_user_foo(list_of_softlinks)

        # Check mount point and brick for the xattr
        self._check_mount_point_and_bricks_for_xattr(list_of_all_files)

        # Check if pathinfo xattr is visible
        self._check_for_trusted_glusterfs_pathinfo(list_of_softlinks)
