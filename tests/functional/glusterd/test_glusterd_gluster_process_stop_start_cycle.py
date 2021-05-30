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

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Description:
    Checking gluster processes stop and start cycle.
"""

from tests.d_parent_test import DParentTest

# disruptive;dist,rep,arb,dist-rep,disp,dist-arb,dist-disp


class TestCase(DParentTest):

    def _wait_for_gluster_process_online_state(self):
        """
        Function which waits for the glusterfs processes to come up
        """
        # Wait for glusterd to be online and validate it's running.
        if not self.redant.wait_for_glusterd_to_start(self.server_list):
            raise Exception("glusterd not up on the desired nodes.")

        # Wait for peers to connect
        if not self.redant.wait_for_peers_to_connect(self.server_list,
                                                     self.server_list[0], 50):
            raise Exception("Peers not in connected state.")

        # Wait for all volume processes to be online
        ret = (self.redant.wait_for_volume_process_to_be_online(self.vol_name,
               self.server_list[0], timeout=600))
        if not ret:
            raise Exception("All volume processes not up.")

    def run_test(self, redant):
        """
        Test Glusterd stop-start cycle of gluster processes.
        1. Create a gluster volume.
        2. Kill all gluster related processes.
        3. Start glusterd service.
        4. Verify that all gluster processes are up.
        5. Repeat the above steps 5 times.
        """
        # Kill all gluster related processes
        for _ in range(5):
            killed_process_count = []
            # Kill gluster processes in all servers
            for server in self.server_list:
                cmd = ('pkill --signal 9 -c -e "(glusterd|glusterfsd|'
                       'glusterfs)"|tail -1')
                ret = redant.execute_abstract_op_node(cmd, server, False)
                if ret['error_code'] != 0:
                    raise Exception(ret['error_msg'])

                killed_process_count.append(int(ret['msg'][0].rstrip('\n')))

            # Start glusterd on all servers.
            redant.start_glusterd(self.server_list)

            # Wait for gluster processes to come up.
            self._wait_for_gluster_process_online_state()

            spawned_process_count = []
            # Get number of  gluster processes spawned in all server
            for server in self.server_list:
                cmd = 'pgrep -c "(glusterd|glusterfsd|glusterfs)"'
                ret = redant.execute_abstract_op_node(cmd, server, False)
                if ret['error_code'] != 0:
                    raise Exception(ret['error_msg'])

                spawned_process_count.append(int(ret['msg'][0].rstrip('\n')))

            # Compare process count in each server.
            for indx, server in enumerate(self.server_list):
                if killed_process_count[indx] != spawned_process_count[indx]:
                    raise Exception("All processes not up and running on"
                                    f" {server}")
