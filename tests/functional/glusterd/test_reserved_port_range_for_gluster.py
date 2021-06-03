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
"""

# disruptive;

from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails in midway
        then the port range needs to be brought
        back to the previous state.
        """
        # Reset port range if some test fails
        if self.port_range_changed:
            cmd = ("sed -i 's/49200/60999/' "
                   "/usr/local/etc/glusterfs/glusterd.vol")
            self.redant.execute_abstract_op_node(cmd, self.server_list[0])

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
        try:

            # Set max port number as 49200 in glusterd.vol file
            cmd = ("sed -i 's/60999/49200/' "
                   "/usr/local/etc/glusterfs/glusterd.vol")
            redant.execute_abstract_op_node(cmd, self.server_list[0])

            self.port_range_changed = True
            # Restart glusterd
            redant.restart_glusterd(self.server_list[0])
            sleep(2)

            # Check node on which glusterd was restarted is back to 'Connected'
            # state from any other peer
            servers = self.server_list[:]
            redant.wait_for_peers_to_connect(servers[0], servers)

            # Create 50 volumes in a loop
            for i in range(1, 51):
                volname = f"{self.vol_name}-volume-{i}"
                redant.volume_create(volname, self.server_list[0],
                                     self.vol_type_inf[self.conv_dict['dist']],
                                     self.server_list, self.brick_roots, True)

            # Try to start 50 volumes in loop
            for i in range(1, 51):
                volname = f"{self.vol_name}-volume-{i}"
                try:
                    ret = redant.volume_start(volname,
                                              self.server_list[0])
                except Exception as error:
                    out = str(error)
                    break

            # Confirm if the 50th volume failed to start
            if i != 50:
                raise Exception("Failed to start volumes 1"
                                " to volume 25 in a loop")

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
                   "/usr/local/etc/glusterfs/glusterd.vol")
            redant.execute_abstract_op_node(cmd, self.server_list[0])

            self.port_range_changed = False

            # Restart glusterd on the same node
            redant.restart_glusterd(self.server_list[0])

            # Starting the 50th volume should succeed now
            # self.volname = "volume-%d" % i
            volname = f"{self.vol_name}-volume-25"

            redant.volume_start(volname,
                                self.server_list[0])

        except Exception as error:
            redant.logger.error(error)
