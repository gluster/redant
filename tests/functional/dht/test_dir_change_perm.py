"""
 Copyright (C) 2018  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check permission change on directories
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
from common.ops.gluster_ops.constants import \
    (FILETYPE_DIRS, TEST_LAYOUT_IS_COMPLETE)
from copy import deepcopy
import traceback
from tests.d_parent_test import DParentTest


class TestDirChangePerm(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Skip for upstream installation for disp,dist-disp vol
        if self.volume_type == "dist-disp" or self.volume_type == "disp":
            self.redant.check_gluster_installation(self.server_list,
                                                   "downstream")

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def terminate(self):
        """
        Delete the users created in the TC
        """
        try:
            for server in self.nodes:
                self.redant.del_user(server, "test_user1")
                self.redant.del_user(server, "test_user2")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        - Create and start a volume
        - Mount it on clients
        - Create 2 test_users on the brick nodes, as well on clients
        - Create some nested dirs, files on mountpoint
        - Validate layout
        - Update owner and permissions of the files on mountpoint
        - Validate updated owner and permissions
        """
        # Create users on all nodes and clients
        self.nodes = self.server_list + [self.client_list[0]]
        for server in self.nodes:
            if not redant.add_user(server, "test_user1"):
                raise Exception("Failed to add user 'test_user1'")
            if not redant.add_user(server, "test_user2"):
                raise Exception("Failed to add user 'test_user2'")

        # Start IO on mounts
        cmd = (f'cd {self.mountpoint} ; mkdir testdir; '
               'mkdir -p testdir/dir{1..10}; touch testdir/file{1..10}')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # List all files and dirs created
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        if not (redant.list_all_files_and_dirs_mounts(self.mounts[0])):
            raise Exception("Failed to list files and dirs")

        # DHT Layout validation
        ret = (redant.validate_files_in_dir(self.client_list[0],
               self.mountpoint, test_type=TEST_LAYOUT_IS_COMPLETE,
               file_type=FILETYPE_DIRS))
        if not ret:
            raise Exception("layout is complete: FAILED")

        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not brick_list:
            raise Exception("Failed to get brick list")

        cmd = (f"find {self.mountpoint} -mindepth 1 -maxdepth 1 -type d | "
               "xargs chown test_user1")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        ret = (redant.compare_dir_structure_mount_with_brick(
               self.client_list[0], self.mountpoint, brick_list, 0))
        if not ret:
            raise Exception("Failed to compare user permission for all files"
                            "/dir in mount directory with brick directory")

        cmd = (f"su -l test_user2 -c \"find {self.mountpoint} -mindepth 1"
               " -maxdepth 1 -type d\"")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = (f"su -l test_user2 -c \"find {self.mountpoint} -mindepth 1"
               " -maxdepth 1 -type d | xargs chmod 777\"")
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception(ret['error_msg'])

        cmd = (f"find {self.mountpoint} -mindepth 1 -maxdepth 1 -type d | "
               "xargs chgrp test_user1")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        ret = (redant.compare_dir_structure_mount_with_brick(
               self.client_list[0], self.mountpoint, brick_list, 1))
        if not ret:
            raise Exception("Failed to compare group permission for all files"
                            "/dir in mount directory with brick directory")

        cmd = (f"su -l test_user2 -c \"find {self.mountpoint} -mindepth 1"
               " -maxdepth 1 -type d\"")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = (f"su -l test_user2 -c \"find {self.mountpoint} -mindepth 1"
               " -maxdepth 1 -type d | xargs chmod 777\"")
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception(ret['error_msg'])

        cmd = (f"find {self.mountpoint} -mindepth 1 -maxdepth 1 -type d "
               "| xargs chmod 777")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        ret = (redant.compare_dir_structure_mount_with_brick(
               self.client_list[0], self.mountpoint, brick_list, 2))
        if not ret:
            raise Exception("Failed to compare permission for all files"
                            "/dir in mount directory with brick directory")

        cmd = (f"su -l test_user2 -c \"find {self.mountpoint} -mindepth 1"
               " -maxdepth 1 -type d\"")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = (f"su -l test_user2 -c \"find {self.mountpoint} -mindepth 1"
               " -maxdepth 1 -type d | xargs chmod 666\"")
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception(ret['error_msg'])
