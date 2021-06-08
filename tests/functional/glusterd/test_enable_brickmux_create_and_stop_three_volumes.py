"""
Copyright (C) 2019  Red Hat, Inc. <http://www.redhat.com>

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
  A testcase to enable cluster.brick-multiplex and create three 1x3
  volumes and stop the volumes.
"""

# disruptive;

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):

        """
        Test Case:
        1.Set cluster.brick-multiplex to enabled.
        2.Create three 1x3 replica volumes.
        3.Start all the three volumes.
        4.Stop three volumes one by one.
        """

        # Timestamp of current test case of start time
        ret = redant.execute_abstract_op_node('date +%s',
                                              self.server_list[0])
        test_timestamp = ret['msg'][0].rstrip("\n")

        # Setting cluster.brick-multiplex to enable
        option = {'cluster.brick-multiplex': 'enable'}
        redant.set_volume_options('all',
                                  option,
                                  self.server_list[0])
        # Create and start 3 volume
        for number in range(1, 4):
            self.volname = f"test_volume_{number}"
            conf_dict = self.vol_type_inf[self.conv_dict["rep"]]
            redant.setup_volume(self.volname,
                                self.server_list[0],
                                conf_dict, self.server_list,
                                self.brick_roots)

        # Checking brick process count.
        for num in range(1, 4):
            self.volname = f"test_volume_{num}"
            brick_list = self.redant.get_all_bricks(self.volname,
                                                    self.server_list[0])
            if brick_list is None:
                raise Exception("Failed to get all bricks: "
                                "Brick list is empty")
            for brick in brick_list:
                server = brick.split(":")[0]
                count = redant.get_brick_processes_count(server)
                if count != 1:
                    raise Exception(f"ERROR: More than one brick process "
                                    f" on {server}.")

        # Stop three volumes one by one.
        for number in range(1, 4):
            self.volname = f"test_volume_{number}"
            redant.volume_stop(self.volname, self.server_list[0])

        # Checking for core files.
        if redant.check_core_file_exists(self.server_list, test_timestamp):
            raise Exception("glusterd service should not have crashed")
