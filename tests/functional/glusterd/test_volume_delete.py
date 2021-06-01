"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
   TC to check volume delete with one brick down
"""

import traceback
#import re
import random
from tests.d_parent_test import DParentTest

# disruptive;dist,rep,dist-rep,disp,dist-disp


class TestCase(DParentTest):

    def terminate(self):
        """Start volume, and glusterd n the random node if something goes
           wrong in betwwen the TC
        """
        try:
            # start glusterd on all servers
            self.redant.start_glusterd(self.server_list)

            if not self.redant.wait_for_glusterd_to_start(self.server_list):
                raise Exception("Failed to start glusterd on all servers")

            # Start volume if stopped
            if not self.vol_started:
                self.redant.volume_start(self.vol_name, self.server_list[0])

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1. Create and start a volume
        2. Get a random brick of the volume
        3. Stop glusterd on the node of the random brick
        4. Try to delete the volume, it should fail
        """
        self.vol_started = True

        # Get the bricks list
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to get the brick list")

        # get a random node other than self.mnode
        if len(bricks_list) >= len(self.server_list):
            random_index = random.randint(1, len(self.server_list) - 1)
        else:
            random_index = random.randint(1, len(bricks_list) - 1)

        # stop glusterd on the random node
        node_to_stop_glusterd = self.server_list[random_index]
        redant.stop_glusterd(node_to_stop_glusterd)

        # stop the volume, it should succeed
        redant.volume_stop(self.vol_name, self.server_list[0])
        self.vol_started = False

        # try to delete the volume, it should fail
        ret = redant.volume_delete(self.vol_name, self.server_lis[0],
                                   False)
        if ret['error_code'] == 0:
            raise Exception("Volume delete succeeded when one of the"
                            " brick node is down")
        # if re.search(r'Some of the peers are down', ret['error_msg']) is None:
        #     raise Exception("Volume delete failed with unexpected error"
        #                     " message")
        redant.logger.info("Error msg: %s, %s", ret['error_msg'], ret['msg'])

        redant.volume_start(self.vol_name, self.server_list[0])
        self.vol_started = True
