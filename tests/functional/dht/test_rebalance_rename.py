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
    Renaming of directories and files while rebalance is running
"""

# disruptive;dist,rep,disp,arb,dist-rep,dist-arb,dist-disp
from copy import deepcopy
import traceback
from tests.d_parent_test import DParentTest


class TestRenameDuringRebalance(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.is_io_running = False
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not self.redant.wait_for_io_to_complete(self.proc,
                                                           self.mounts):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test file renames during rebalance
        - Create a volume
        - Create directories or files
        - Calculate the checksum using arequal
        - Add brick and start rebalance
        - While rebalance is running, rename files or directories.
        - After rebalancing calculate checksum.
        """
        # Creating main directory.
        redant.create_dir(self.mountpoint, "main", self.client_list[0])

        # Creating Files.
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        proc = redant.create_files("1k", f"{self.mountpoint}/main/",
                                   self.client_list[0], 4000)

        # Wait for IO completion.
        if not redant.validate_io_procs(proc, self.mounts):
            raise Exception("IO failed on some of the clients")

        # Getting the arequal checksum.
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts)

        # Log Volume Info and Status before expanding the volume.
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.volname}")

        # Expanding volume by adding bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to expand the volume {self.vol_name}")

        # Log Volume Info and Status after expanding the volume.
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.volname}")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Check that rebalance status is "in progress"
        rebalance_status = redant.get_rebalance_status(self.vol_name,
                                                       self.server_list[0])
        if rebalance_status['aggregate']['statusStr'] != "in progress":
            raise Exception("Rebalance is not in 'in progress' state, either "
                            "rebalance is in completed state or failed to"
                            " get rebalance status")

        # Renaming the files during rebalance.
        cmd = ("python3 /usr/share/redant/script/file_dir_ops.py mv"
               f" {self.mountpoint}/main/ --postfix re ")
        self.proc = redant.execute_command_async(cmd, self.client_list[0])
        self.is_io_running = True

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0])
        if not ret:
            raise Exception("Rebalace is not yet complete on the volume "
                            f"{self.vol_name}")

        # Wait for IO completion.
        if not redant.validate_io_procs(self.proc, self.mounts):
            raise Exception("IO failed on some of the clients")
        self.is_io_running = False

        # Getting arequal checksum after rebalance
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts)

        # Comparing arequals checksum before and after rebalance.
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum is NOT MATCHING")
