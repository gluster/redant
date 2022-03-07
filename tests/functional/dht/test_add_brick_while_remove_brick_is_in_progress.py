"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check add-brick while remove brick is in progress
"""

# disruptive;dist,dist-rep,dist-disp
from common.ops.gluster_ops.constants import (FILETYPE_DIRS,
                                              TEST_LAYOUT_IS_COMPLETE)
from copy import deepcopy
import traceback
from tests.d_parent_test import DParentTest


class TestRemoveBrickValidation(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Skip for upstream installation for dist-disp vol
        if self.volume_type == "dist-disp":
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
        Stop remove brick operation, if the status is 'in-progress'
        """
        try:
            if self.remove_brick_list:
                status_info = (self.redant.get_remove_brick_status(
                               self.server_list[0], self.vol_name,
                               self.remove_brick_list))
                if 'in progress' in status_info['aggregate']['statusStr']:
                    # Shrink volume by removing bricks with option start
                    self.redant.remove_brick(self.server_list[0],
                                             self.vol_name,
                                             self.remove_brick_list, "stop")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        - Create and start a volume
        - Mount the volume on a client
        - Form brick list for expanding volume
        - Start IO on mountpoint
        - Validate IO
        - Verify hash layout values
        - Form brick list to remove bricks
        - Start removing bricks
        - Start add-brick, and confirm that it fails with proper error msg
        - Cleanup the brick directories created
        - Stop remove brick, if the status is 'in-progress'
        """
        self.remove_brick_list = []

        # Form brick list for expanding volume
        add_brick_cmd = (redant.form_brick_cmd_to_add_brick(
                         self.server_list[0], self.vol_name,
                         self.server_list, self.brick_roots,
                         distribute_count=1))
        if not add_brick_cmd:
            raise Exception("Failed to form add-brick cmd")

        # Start IO on mounts
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        all_mounts_procs = []
        for index, mount_obj in enumerate(self.mounts, start=1):
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      index + 10, 2, 4, 4,
                                                      25, mount_obj['client'])
            all_mounts_procs.append(proc)

        # Wait for IO to complete
        ret = redant.validate_io_procs(all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # List all files and dirs created
        if not redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to find list and dirs opn mountpoints")

        # DHT Layout and hash validation
        ret = (redant.validate_files_in_dir(self.client_list[0],
               self.mountpoint, test_type=TEST_LAYOUT_IS_COMPLETE,
               file_type=FILETYPE_DIRS))
        if not ret:
            raise Exception("LAYOUT_IS_COMPLETE: FAILED")

        # Log Volume Info and Status before shrinking the volume.
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Form bricks list for volume shrink
        self.remove_brick_list = (redant.form_bricks_list_to_remove_brick(
                                  self.server_list[0], self.vol_name,
                                  subvol_num=1))
        if self.remove_brick_list is None:
            raise Exception(f"Volume {self.vol_name}: Failed to form bricks"
                            " list for shrink")

        # Shrink volume by removing bricks
        redant.remove_brick(self.server_list[0], self.vol_name,
                            self.remove_brick_list, "start")

        # Log remove-brick status
        redant.remove_brick(self.server_list[0], self.vol_name,
                            self.remove_brick_list, "status")

        # Expanding volume while volume shrink is in-progress
        ret = redant.add_brick(self.vol_name, add_brick_cmd,
                               self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully added"
                            "bricks to the volume")

        if "rebalance is in progress" not in ret['msg']['opErrstr']:
            raise Exception("add-brick failed with wrong error")

        # cleanup add-bricks list
        add_brick_list = add_brick_cmd.split()
        ret = redant.delete_bricks(add_brick_list)
        if not ret:
            raise Exception("Failed to cleanup bricks")
