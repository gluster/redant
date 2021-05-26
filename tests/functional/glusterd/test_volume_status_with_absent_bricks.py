"""
Copyright (C) 2018-2020 Red Hat, Inc. <http://www.redhat.com>

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

Description: Volume start when one of the brick is absent
"""

import random
from tests.d_parent_test import DParentTest

# disruptive;dist,rep,dist-rep,disp,dist-disp,arb,dist-arb


class TestCase(DParentTest):
    def run_test(self, redant):
        """
        Test Case:
        1) Create Volume
        2) Remove any one Brick directory
        3) Start Volume and compare the failure message
        4) Check the gluster volume status and compare the status message
        """
        # Fetching the brick list
        redant.logger.info("Fetch all the bricks of the volume")
        brick_list = redant.es.get_brickdata(self.vol_name)
        if brick_list is None:
            raise Exception("Failed to get the brick list")

        # Removing any one brick directory
        brick_list = list(brick_list.items())
        random_brick = random.choice(brick_list)
        random_brick_path = random.choice(random_brick[1])
        cmd = f'rm -rf {random_brick_path}'
        redant.execute_abstract_op_node(cmd, random_brick[0])
        redant.logger.info("Brick directory removed successfully")

        redant.volume_stop(self.vol_name, self.server_list[0])
        # Starting volume
        err_msg = 'Failed to find brick directory'
        cmd = f"gluster volume start {self.vol_name}"
        ret = redant.execute_command(cmd, self.server_list[0])
        if err_msg not in ret['error_msg']:
            raise Exception("Unexpected!!")
        try:
            redant.volume_start(self.vol_name, self.server_list[0])
        except:
            redant.logger.info(f"Expected: Failed to start volume"
                               f"{self.vol_name}")

        # Checking volume status
        cmd = f'gluster vol status {self.vol_name}'
        ret = redant.execute_command(cmd, self.server_list[0])
        if ret['error_msg'] != f'Volume {self.vol_name} is not started\n':
            raise Exception("Volume status erraneous")

        try:
            redant.get_volume_status(self.vol_name, self.server_list[0])
        except:
            redant.logger.info("Volume hasn't started hence no status for it.")
