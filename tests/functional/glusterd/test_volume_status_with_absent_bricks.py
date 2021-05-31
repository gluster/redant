'''
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
'''

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
        # Stopping the volume
        redant.volume_stop(self.vol_name, self.server_list[0])

        # Fetching the brick list
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get the bricks in"
                            " the volume")

        # Removing any one brick directory
        random_brick = random.choice(brick_list)
        node, brick_path = random_brick.split(':')
        cmd = 'rm -rf ' + brick_path
        redant.execute_abstract_op_node(cmd, node)

        # Starting volume
        err_msg = 'Failed to find brick directory'
        ret = redant.volume_start(self.vol_name, self.server_list[0],
                                  excep=False)
        if ret['error_code'] != 0 and err_msg not in ret['msg']['opErrstr']:
            raise Exception("Unexpected:Volume started successfully"
                            " even though brick is deleted.")

        # Checking volume status
        ret = redant.get_volume_status(self.vol_name, self.server_list[0],
                                       excep=False)
        if ret['error_code'] != 0 and ret['msg']['opErrstr'] != \
        f'Volume {self.vol_name} is not started':
            raise Exception("Incorrect error message for gluster vol "
                            "status")
