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
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

  Description:
  Stopping glusterd while doing rebalance operations and
  fetch volume status.
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;dist-rep


class TestCase(DParentTest):
    """
    xml Dump of gluster volume status during rebalance, when one gluster
    node is down
    """

    def terminate(self):
        """
        The voume created in the test case is destroyed.
        """
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")
            self.redant.cleanup_volume(self.volume_name1, self.server_list[0])
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        1. Create a trusted storage pool by peer probing the node
        2. Create a distributed-replicated volume
        3. Start the volume and fuse mount the volume and start IO
        4. Create another replicated volume and start it and stop it
        5. Start rebalance on the volume
        6. While rebalance in progress, stop glusterd on one of the nodes
            in the Trusted Storage pool.
        7. Get the status of the volumes with --xml dump
        """

        self.volume_type1 = 'rep'
        self.volume_name1 = f"{self.test_name}-{self.volume_type1}-1"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
        redant.setup_volume(self.volume_name1, self.server_list[0],
                            conf_dict, self.server_list,
                            self.brick_roots, True)

        # Start IO on mounts
        counter = 1
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 3, 4, 10,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter = counter + 10

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")

        ret = redant.volume_stop(self.volume_name1, self.server_list[0])

        # Start Rebalance
        ret = redant.rebalance_start(self.vol_name, self.server_list[0])

        # Get rebalance status
        status_info = redant.get_rebalance_status(self.vol_name,
                                                  self.server_list[0])
        status = status_info['aggregate']['statusStr']

        if 'in progress' not in status:
            raise Exception("Rebalance process is not running")

        redant.logger.info("Rebalance process is running")

        # Stop glusterd
        redant.stop_glusterd(self.server_list[2])

        cmd = ("gluster v status  | grep -A 4 'Rebalance' | awk 'NR==3{print "
               "$3,$4}'")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        ret1 = redant.get_volume_status(self.vol_name, self.server_list[0],
                                        options="tasks")
        rebalance_status = ret1[self.vol_name]['task_status'][0]['statusStr']
        if rebalance_status not in " ".join(ret['msg']).replace("\n", ""):
            raise Exception("rebalance status is not in volume status")
