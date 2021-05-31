"""
  Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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
  Testing rebalance operations when io operations are performed
  and an extra brick is added.
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")
            self.redant.cleanup_volume(self.volume_name1, self.server_list[0])
        except Exception as e:
            tb = traceback.format_exc()
            self.redant.logger.error(e)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1) Create a distributed volume
        2) Perform io operations
        3) Add brick
        4) Start Rebalance
        5) Peer Probe new node
        6) Get rebalance status
        """
        self.volume_type1 = 'dist'
        self.volume_name1 = f"{self.test_name}-{self.volume_type1}-1"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
        redant.setup_volume(self.volume_name1, self.server_list[0], conf_dict,
                            self.server_list[0:2], self.brick_roots, True)
        self.mountpoint = (f"/mnt/{self.volume_name1}")
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        redant.volume_mount(self.server_list[0], self.volume_name1,
                            self.mountpoint, self.client_list[0])

        # run IOs
        redant.logger.info("Starting IO on all mounts...")
        self.all_mounts_procs = []
        counter = 1
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.volume_name1)
        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 3, 4, 10,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter = counter + 10

        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO operations failed on some"
                            " or all of the clients")

        # add a brick to the volume and start rebalance
        mul_factor = 1
        _, brick_cmd = redant.form_brick_cmd(self.server_list,
                                             self.brick_roots,
                                             self.volume_name1, mul_factor,
                                             True)
        redant.add_brick(self.volume_name1, brick_cmd[1:],
                         self.server_list[0])
        self.vol_type_inf[self.conv_dict[self.volume_type1]]['dist_count'] += 1

        redant.rebalance_start(self.volume_name1, self.server_list[0])

        # peer probe a new node from existing cluster
        redant.peer_probe(self.server_list[2], self.server_list[0])

        ret = redant.get_rebalance_status(self.volume_name1,
                                          self.server_list[0])
        if ret is None:
            raise Exception("Rebalance status command has returned None")
