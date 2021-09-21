"""
Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
"""

# nonDisruptive;dist,dist-rep,dist-disp,dist-arb
import traceback
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):
    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_perm_set:
                if not (self.redant.set_file_permissions(self.client_list[0],
                        self.mountpoint, "755")):
                    raise Exception("Failed to reset permission on mountpoint")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _set_root_dir_permission(self, permission):
        """ Sets the root dir permission to the given value"""
        ret = self.redant.set_file_permissions(self.client_list[0],
                                               self.mountpoint,
                                               permission)
        if not ret:
            raise Exception("Failed to set permissions on the mountpoint")

    def _get_dir_permissions(self, node, path):
        """ Returns dir permissions"""
        cmd = f'stat -c "%a" {path}'
        out = self.redant.execute_abstract_op_node(cmd, node)
        return out['msg'][0].strip()

    def _get_root_dir_permission(self, expected=None):
        """ Returns the root dir permission """
        permission = self._get_dir_permissions(self.client_list[0],
                                               self.mountpoint)
        if not expected:
            return permission

        if permission != expected:
            raise Exception("The permissions doesn't match")

        return True

    def _bring_a_brick_offline(self):
        """ Brings down a brick from the volume"""
        brick_to_kill = self.redant.get_all_bricks(self.vol_name,
                                                   self.server_list[0])[-1]
        if not self.redant.bring_bricks_offline(self.vol_name,
                                                brick_to_kill):
            raise Exception("Failed to bring down the bricks.")
        return brick_to_kill

    def _bring_back_brick_online(self, brick):
        """ Brings back down brick from the volume"""
        if not self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                               brick, True):
            raise Exception("Failed to bring the brick "
                            f"{brick} online")

    def _verify_mount_dir_and_brick_dir_permissions(self, expected,
                                                    down_brick=None):
        """ Verifies the mount directory and brick dir permissions are same"""
        # Get root dir permission and verify
        self._get_root_dir_permission(expected)

        # Verify brick dir permission
        brick_list = self.redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
        for brick in brick_list:
            brick_node, brick_path = brick.split(":")
            if down_brick and down_brick.split(":")[-1] != brick_path:
                actual_perm = self._get_dir_permissions(brick_node,
                                                        brick_path)
                if actual_perm != expected:
                    raise Exception("The permissions are not same")

    def run_test(self, redant):
        """
        1. create pure dist volume
        2. mount on client
        3. Checked default permission (should be 755)
        4. Change the permission to 444 and verify
        5. Kill a brick
        6. Change root permission to 755
        7. Verify permission changes on all bricks, except down brick
        8. Bring back the brick and verify the changes are reflected
        """
        self.is_perm_set = False
        # Verify the default permission on root dir is 755
        self._verify_mount_dir_and_brick_dir_permissions("755")

        # Change root permission to 444
        self._set_root_dir_permission("444")
        self.is_perm_set = True

        # Verify the changes were successful
        self._verify_mount_dir_and_brick_dir_permissions("444")

        # Kill a brick
        offline_brick = self._bring_a_brick_offline()

        # Change root permission to 755
        self._set_root_dir_permission("755")
        self.is_perm_set = False

        # Verify the permission changed to 755 on mount and brick dirs
        self._verify_mount_dir_and_brick_dir_permissions("755", offline_brick)

        # Bring brick online
        self._bring_back_brick_online(offline_brick)

        # Verify the permission changed to 755 on mount and brick dirs
        self._verify_mount_dir_and_brick_dir_permissions("755")

        redant.logger.info("Test to verify permission changes made on"
                           " mount dir i succesful")
