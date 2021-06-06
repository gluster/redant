"""
  Copyright (C) 2019-2020  Red Hat, Inc. <http://www.redhat.com>

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
  Changing reserve limits to higher and lower limits and
  performing io operations

"""

import traceback
from tests.nd_parent_test import NdParentTest


# nonDisruptive;dist-rep
class TestChangeReservcelimit(NdParentTest):

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

    def set_storage_reserve_value(self, redant, vol_name, storage_res_val):
        """
        Test Case:
        1) Create a distributed-replicated volume and start it.
        2) Enable storage.reserve option on the volume using below command:
            gluster volume set <volname> storage.reserve <value>
        3) Mount the volume on a client.
        4) Write some data on the mount points.
        5) Start remove-brick operation.
        6) While remove-brick is in-progress change the reserve limit to a
           lower or higher value.
        """
        counter = 1

        # Setting storage.reserve to 50
        redant.set_volume_options(vol_name, {'storage.reserve': '50'},
                                  self.server_list[0])

        # Run IOs
        redant.logger.info("Starting IO on all mounts...")
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(vol_name)
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

        brick_list = redant.get_all_bricks(vol_name, self.server_list[0])

        # Remove brick
        ret = redant.remove_brick(self.server_list[0], vol_name,
                                  brick_list[-3:], 'start', 3)

        if ret['error_code'] != 0:
            raise Exception("Failed to start remove brick operation.")

        # Setting storage.reserve to 33 or 99
        redant.set_volume_options(vol_name,
                                  {'storage.reserve': storage_res_val},
                                  self.server_list[0])

        ret = redant.remove_brick(self.server_list[0], vol_name,
                                  brick_list[-3:], 'stop', 3)

        if ret['error_code'] != 0:
            raise Exception("Failed to stop remove brick operation.")

    def run_test(self, redant):
        """
        Steps:
        1) Change the reserve limit to a lower value.
        2) Create a new distributed-replicated volume for setting
           reserve limit to a higher value.
        3) Change the reserve limit to a higher value on the newly created
           volume
        """
        # change_reserve_limit_to_lower_value
        self.set_storage_reserve_value(redant, self.vol_name, "33")
        # volume creation for setting reserve limit to higher value.
        self.volume_type1 = 'dist-rep'
        self.volume_name1 = f"{self.test_name}-1"
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]
        redant.setup_volume(self.volume_name1, self.server_list[0],
                            conf_dict, self.server_list,
                            self.brick_roots, True)
        mountpoint = f"/mnt/{self.volume_name1}"
        redant.execute_abstract_op_node(f"mkdir -p {mountpoint}",
                                        self.client_list[0])
        redant.volume_mount(self.server_list[0], self.volume_name1,
                            mountpoint, self.client_list[0])

        # change_reserve_limit_to_higher_value is a seperate test case
        # which is being merged into a single test case
        self.set_storage_reserve_value(redant, self.volume_name1, "99")
