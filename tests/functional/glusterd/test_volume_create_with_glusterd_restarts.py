'''
Copyright (C) 2017-2020 Red Hat, Inc. <http://www.redhat.com>

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
This test deals with volume creation with glusterd restarts.
'''

# disruptive;dist

import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        pass

    def terminate(self):
        """
        To peer probe all the servers
        """
        try:
            # wait till peers are in connected state
            if not (self.redant.
                    wait_for_peers_to_connect(self.server_list,
                                              self.server_list[0],
                                              60)):
                raise Exception("Failed to connect peers")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _glusterd_restart_async(self):
        # Restarting glusterd in a loop
        restart_cmd = ("for i in `seq 1 5`; do "
                       "service glusterd restart; "
                       "systemctl reset-failed glusterd; "
                       "sleep 3; "
                       "done")
        proc1 = self.redant.execute_command_async(restart_cmd,
                                                  self.server_list[3])

        # After running restart in async adding 10 sec sleep
        sleep(10)
        return proc1

    def _check_process_ended(self, proc1):
        # check if the process ended successfully
        ret = self.redant.wait_till_async_command_ends(proc1)
        if ret['error_code'] != 0:
            raise Exception("Glusterd restart not working")

    def run_test(self, redant):
        """
        Test case:
        1) Create a cluster.
        2) Create volume using the first three nodes say N1, N2 and N3.
        3) While the create is happening restart the fourth node N4.
        4) Check if glusterd has crashed on any node.
        5) While the volume start is happening restart N4.
        6) Check if glusterd has crashed on any node.
        """
        if len(self.server_list) < 4:
            self.TEST_RES = None
            raise Exception("Minimum 4 nodes required for this TC to run")

        # Fetching all the parameters for volume_create
        list_of_three_servers = self.server_list[0:3]

        # Restarting glusterd in a loop
        proc1 = self._glusterd_restart_async()

        # Creating volumes using 3 servers
        self.volume_type = "dist"
        self.vol_name = (f"{self.test_name}-{self.volume_type}")
        conf_hash = self.vol_type_inf[self.volume_type]
        redant.volume_create(self.vol_name, self.server_list[0], conf_hash,
                             list_of_three_servers, self.brick_roots)
        # check if process ended
        self._check_process_ended(proc1)

        # Checking if peers are connected or not.
        if not redant.wait_for_peers_to_connect(self.server_list,
                                                self.server_list[0],
                                                60):
            raise Exception("Peers are not connected")

        # Restarting glusterd in a loop
        proc1 = self._glusterd_restart_async()

        # Start the volume created.
        redant.volume_start(self.vol_name, self.server_list[0])

        # check if process ended
        self._check_process_ended(proc1)

        # Checking if peers are connected or not.
        if not redant.wait_for_peers_to_connect(self.server_list,
                                                self.server_list[0],
                                                60):
            raise Exception("Peers are not connected")
