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
    Test remove-brick operation when quorum not met
"""

# disruptive;dist,disp,dist-disp
import random
from tests.d_parent_test import DParentTest


class TestServerQuorumNotMet(DParentTest):

    def run_test(self, redant):
        '''
        -> Create volume
        -> Enabling server quorum
        -> Set server quorum ratio to 95%
        -> Stop the glusterd on any one of the node
        -> Perform remove brick operation
        -> start glusterd
        -> Check gluster vol info, bricks should be same before and after
        performing remove brick operation.
        '''
        # Enabling server quorum
        redant.set_volume_options(self.vol_name,
                                  {'cluster.server-quorum-type': 'server'},
                                  self.server_list[0])

        # Setting server quorum ratio in percentage
        redant.set_volume_options('all',
                                  {'cluster.server-quorum-ratio': '95%'},
                                  self.server_list[0])

        # Getting brick list from volume
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception(f"Failed to get brick list of {self.vol_name}")

        # Stopping glusterd
        self.random_server = random.choice(self.server_list[1:])
        redant.stop_glusterd(self.random_server)
        if not redant.wait_for_glusterd_to_stop(self.random_server):
            raise Exception("Failed to stop glusterd on node "
                            f"{self.random_server}")

        # Forming brick list for performing remove brick operation
        rmve_brk_list = (redant.form_bricks_list_to_remove_brick(
                         self.server_list[0], self.vol_name))
        if rmve_brk_list is None:
            raise Exception("Failed to get brick list for performing "
                            "remove-brick operation")

        # Performing remove brick operation
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  rmve_brk_list, 'force', excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: remove-brick operation should have"
                            " failed when quorum not met")

        # Expected error message for remove brick operation
        msg = "Quorum not met. Volume operation not allowed"

        if msg not in ret['msg']['opErrstr']:
            raise Exception("Error message is not correct for "
                            "remove brick operation when quorum not met")

        # Starting glusterd
        redant.start_glusterd(self.random_server)

        # Checking glusterd status
        if not redant.wait_for_glusterd_to_start(self.random_server):
            raise Exception("Failed to start glusterd on node "
                            f"{self.random_server}")

        # Getting brick list of volume after performing remove brick operation
        new_brick_list = redant.get_all_bricks(self.vol_name,
                                               self.server_list[0])
        if new_brick_list is None:
            raise Exception(f"Failed to get brick list of {self.vol_name}")

        # Comparing bricks info before and after performing
        # remove brick operation
        if new_brick_list != brick_list:
            raise Exception("Bricks are not same before and after performing"
                            " remove brick operation")
