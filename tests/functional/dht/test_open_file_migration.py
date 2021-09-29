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
    TC checks that files with open fd are migrated successfully.
"""

# disruptive;dist,rep,arb,disp
import traceback
from tests.d_parent_test import DParentTest


class TestOpenFileMigration(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails midway
        """
        try:
            if self.is_io_running:
                ret = self.redant.wait_till_async_command_ends(self.proc)
                if ret['error_code'] != 0:
                    raise Exception("Write on open fd has not completed yet")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps :
        1) Create a volume.
        2) Mount the volume using FUSE.
        3) Create files on volume mount.
        4) Open fd for the files and keep on doing read write operations on
           these files.
        5) While fds are open, add bricks to the volume and trigger rebalance.
        6) Wait for rebalance to complete.
        7) Wait for write on open fd to complete.
        8) Check for any data loss during rebalance.
        9) Check if rebalance has any failures.
        """
        self.is_io_running = False

        # Create files and open fd for the files on mount point
        cmd = (f"cd {self.mountpoint}; for i in `seq 261 1261`;do touch "
               "testfile$i; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])
        self.proc = redant.open_file_fd(self.mountpoint, 2,
                                        self.client_list[0], start_range=301,
                                        end_range=400)
        self.is_io_running = True

        # Calculate file count for the mount-point
        cmd = f"ls -lR {self.mountpoint}/testfile* | wc -l"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        count_before = int(ret['msg'][0].strip())

        # Add bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to expand the volume {self.vol_name}")

        # Trigger rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0])
        if not ret:
            raise Exception(f"Rebalance failed on volume {self.vol_name}")

        # Close connection and check if write on open fd has completed
        ret = redant.wait_till_async_command_ends(self.proc)
        if ret['error_code'] != 0:
            raise Exception("Write on open fd"
                            " has not completed yet")
        self.is_io_running = False

        # Calculate file count for the mount-point
        cmd = f"ls -lR {self.mountpoint}/testfile* | wc -l"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        count_after = int(ret['msg'][0].strip())

        # Check if there is any data loss
        if count_before != count_after:
            raise Exception("The file count before and after"
                            " rebalance is not same."
                            " There is data loss.")

        # Check if rebalance has any failures
        ret = redant.get_rebalance_status(self.vol_name, self.server_list[0])
        no_of_failures = ret['aggregate']['failures']
        if int(no_of_failures) != 0:
            raise Exception("Failures in rebalance")
