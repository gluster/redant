"""
  Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test restart glusterd while rebalance is in progress
"""

import traceback
from tests.d_parent_test import DParentTest


# disruptive;dist,rep,dist-rep
# TODO: Add disp and dist-disp volume_types to run

class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway then wait for IO to comlete before
        calling the terminate function of DParentTest
        """
        try:
            ret = self.redant.wait_for_io_to_complete(self.list_of_procs,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        1) Create Volume
        2) Fuse mount the volume
        3) Perform I/O on fuse mount
        4) Add bricks to the volume
        5) Perform rebalance on the volume
        6) While rebalance is in progress,
        7) restart glusterd on all the nodes in the cluster
        """

        # run IO on mountpoint
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.list_of_procs = []
        self.counter = 1
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      self.counter,
                                                      2, 5, 3, 10,
                                                      mount_obj['client'])

            self.list_of_procs.append(proc)
            self.counter += 10

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        if self.volume_type != 'dist':
            mul_factor = 3

            # forming brick list
            _, br_cmd = redant.form_brick_cmd(self.server_list,
                                              self.brick_roots,
                                              self.vol_name, mul_factor, True)
            # add brick
            kwargs = {'replica_count': 3}
            redant.add_brick(self.vol_name, br_cmd, self.server_list[0],
                             False, True, **kwargs)
        else:
            mul_factor = 1

            # forming brick list
            _, br_cmd = redant.form_brick_cmd(self.server_list,
                                              self.brick_roots,
                                              self.vol_name, mul_factor, True)
            # add brick
            redant.add_brick(self.vol_name, br_cmd,
                             self.server_list[0])

        # Performing rebalance
        ret = redant.rebalance_start(self.vol_name, self.server_list[0])

        # Checking Rebalance is in progress or not
        rebalance_status = redant.get_rebalance_status(self.vol_name,
                                                       self.server_list[0])
        if rebalance_status is None:
            raise Exception("Rebalance status returned None")

        if rebalance_status['aggregate']['statusStr'] != 'in progress':
            raise Exception("Rebalance is not in 'in progress' state, "
                            "either rebalance is in compeleted state or"
                            " failed to get rebalance status")

        # Restart glusterd
        redant.restart_glusterd(self.server_list)

        # Checking glusterd status
        ret = redant.wait_for_glusterd_to_start(self.server_list)
        if not ret:
            raise Exception("Glusterd is not running on some of the "
                            "servers")
