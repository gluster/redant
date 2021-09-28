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
51 Franklin Street, Fifth Floor, Boston, MA 02110-131 USA.

Description:
    Rebalance with special files
"""

# disruptive;dist,dist-arb,dist-rep,dist-disp

import traceback
from tests.d_parent_test import DParentTest


class TestRebalanceWithSpecialFiles(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails early
        """
        try:
            if not self.io_validation_complete:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mounts)):
                    raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Rebalance with special files
        - Create Volume and start it.
        - Create some special files on mount point.
        - Once it is complete, start some IO.
        - Add brick into the volume and start rebalance
        - All IO should be successful.
        """
        # Create pipe files at mountpoint.
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        mpoint = self.mountpoint
        cmd = ("for i in {1..500};do mkfifo %s/fifo${i}; done" % mpoint)
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create block device files at mountpoint.
        cmd = ("for i in {1..500};"
               "do mknod %s/blk${i} blockfile 1 5;done" % mpoint)
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create character device files at mountpoint.
        cmd = ("for i in {1..500};"
               "do mknod %s/charc${i} characterfile 1 5;done" % mpoint)
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create files at mountpoint.
        self.io_validation_complete = True
        self.all_mounts_procs = []
        proc = redant.create_files(num_files=1000,
                                   fix_fil_size="1M",
                                   path=mpoint,
                                   node=self.client_list[0])
        self.all_mounts_procs.append(proc)
        self.io_validation_complete = False

        # Log the volume info and status before expanding volume.
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Expand the volume.
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=True)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Log the volume info after expanding volume.
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Start Rebalance.
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Check rebalance is in progress
        status_info = redant.get_rebalance_status(self.vol_name,
                                                  self.server_list[0])
        status = status_info['aggregate']['statusStr']
        if status != "in progress":
            raise Exception("Rebalance is not in 'in progress' state, either "
                            "rebalance is in completed state or failed to get"
                            " rebalance status")

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=600)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Wait for IO to complete.
        ret = redant.wait_for_io_to_complete(self.all_mounts_procs,
                                             self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")
        self.io_validation_complete = True
