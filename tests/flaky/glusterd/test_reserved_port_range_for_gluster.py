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
  Setting reserved port range for gluster

*Flaky Test*
Reason: Sometimes expected number of free ports are not available in the CI
"""

# disruptive;
import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails in midway
        then the port range needs to be brought
        back to the previous state.
        """
        try:
            # Reset port range if some test fails
            if self.port_range_changed:
                cmd = ("sed -i 's/49200/60999/' "
                       "/etc/glusterfs/glusterd.vol")
                self.redant.execute_abstract_op_node(cmd, self.server_list[0])

            # Restart glusterd to update the port range
            self.redant.restart_glusterd(self.server_list)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test Case:
        1) Set the max-port option in glusterd.vol file to 49200
        2) Restart glusterd on one of the node
        3) Create 50 volumes in a loop
        4) Try to start the 50 volumes in a loop
        5) Confirm that the 50th volume failed to start
        6) Confirm the error message, due to which volume failed to start
        7) Set the max-port option in glusterd.vol file back to default value
        8) Restart glusterd on the same node
        9) Starting the 50th volume should succeed now
        """
        self.port_range_changed = False

        # Set max port number as 49200 in glusterd.vol file
        cmd = ("sed -i 's/60999/49200/' "
               "/etc/glusterfs/glusterd.vol")
        redant.execute_abstract_op_node(cmd, self.server_list[0])

        self.port_range_changed = True
        # Restart glusterd
        redant.restart_glusterd(self.server_list[0])
        if not redant.wait_for_glusterd_to_start(self.server_list[0]):
            raise Exception(f"Glusterd did not start "
                            f"for {self.server_list[0]}")

        # Check node on which glusterd was restarted is back to 'Connected'
        # state from any other peer
        if not redant.wait_for_peers_to_connect(self.server_list,
                                                self.server_list[1]):
            raise Exception("Peers node in connected mode.")

        # Create 50 volumes in a loop
        for i in range(1, 51):
            volname = f"{self.vol_name}-volume-{i}"
            redant.volume_create(volname, self.server_list[0],
                                 self.vol_type_inf['dist'],
                                 self.server_list, self.brick_roots, True)

        # Try to start 50 volumes in loop
        out = ''
        for i in range(1, 51):
            volname = f"{self.vol_name}-volume-{i}"
            ret = redant.volume_start(volname, self.server_list[0],
                                      excep=False)
            if ret['msg']['opRet'] != '0':
                redant.logger.info(f"Failed to start volume {volname}")
                out = ret['msg']['opErrstr']
                break

        # Confirm if the 50th volume failed to start
        if i != 50:
            raise Exception("Failed to start volumes 1"
                            " to volume 49 in a loop")

        # Confirm the error message on volume start fail
        err_msg = ("Commit failed on localhost. "
                   "Please check log file for details.")

        if out != err_msg:
            raise Exception("Volume start didn't fail with the "
                            "expected error message")

        # Confirm the error message from the log file
        cmd = ("cat /var/log/glusterfs/glusterd.log | "
               "grep -i 'All the ports in the range are"
               " exhausted' | wc -l")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])

        out = ret['msg'][0].rstrip('\n')
        if int(out) == 0:
            raise Exception("Volume start didn't fail with expected"
                            " error message")

        # Set max port number back to default value in glusterd.vol file
        cmd = ("sed -i 's/49200/60999/' "
               "/etc/glusterfs/glusterd.vol")
        redant.execute_abstract_op_node(cmd, self.server_list[0])

        self.port_range_changed = False

        # Restart glusterd on the same node
        redant.restart_glusterd(self.server_list[0])
        if not redant.wait_for_glusterd_to_start(self.server_list[0]):
            raise Exception(f"Glusterd did not start "
                            f"for {self.server_list[0]}")
        # Starting the 50th volume should succeed now
        # self.volname = "volume-%d" % i
        volname = f"{self.vol_name}-volume-50"

        redant.volume_start(volname,
                            self.server_list[0])
