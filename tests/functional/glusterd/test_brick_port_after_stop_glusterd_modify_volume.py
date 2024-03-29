"""
  Copyright (C) 2020  Red Hat, Inc. <http://www.redhat.com>

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
  Testing brick port allocation after stopping glusterd,
  making changes on the volume and starting the glusterd
  again.
"""

from time import sleep
from copy import deepcopy
from tests.d_parent_test import DParentTest


# disruptive;dist
class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 2
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)

    def run_test(self, redant):
        """
        In this test case:
        1. Stop glusterd on node 2.
        2. Modify any of the volume option on node 1
        3. Start glusterd on node 2
        4. Check volume status, brick should get port
        """
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to get the brick list")

        vol_status = redant.get_volume_status(self.vol_name,
                                              self.server_list[0])
        if vol_status is None:
            raise Exception("Failed to get volume "
                            f"status for {self.vol_name}")

        vol_bricks = vol_status[self.vol_name]['node']
        if not isinstance(vol_bricks, list):
            vol_bricks = [vol_bricks]
        totport = 0
        for vol_brick in vol_bricks:
            if vol_brick["port"] == 'N/A':
                continue
            if int(vol_brick["port"]) > 0:
                totport += 1

        if totport != 2:
            raise Exception(f"Volume {self.vol_name} is not started "
                            "successfully because no. of brick port "
                            "is not equal to 2")

        redant.stop_glusterd(self.server_list[1])
        redant.wait_for_glusterd_to_stop(self.server_list[1])

        option = {'performance.readdir-ahead': 'on'}
        ret = redant.set_volume_options(self.vol_name, option,
                                        self.server_list[0])

        redant.start_glusterd(self.server_list[1])
        redant.wait_for_glusterd_to_start(self.server_list[1])

        ret = redant.wait_for_peers_to_connect(self.server_list[1],
                                               self.server_list[0])
        if not ret:
            raise Exception("glusterd is not connected "
                            f"{self.server_list[0]} with peer "
                            f"{self.server_list[1]}")

        # Waiting for 10 sec so that the brick will get port
        sleep(10)
        vol_status = redant.get_volume_status(self.vol_name,
                                              self.server_list[0])
        if vol_status is None:
            raise Exception("Failed to get volume "
                            f"status for {self.vol_name}")

        vol_bricks = vol_status[self.vol_name]['node']
        if not isinstance(vol_bricks, list):
            vol_bricks = [vol_bricks]
        totport = 0
        for vol_brick in vol_bricks:
            if vol_brick["port"] == 'N/A':
                continue
            if int(vol_brick["port"]) > 0:
                totport += 1

        if totport != 2:
            raise Exception(f"Volume {self.vol_name} is not started "
                            "successfully because no. of brick port "
                            "is not equal to 2")
