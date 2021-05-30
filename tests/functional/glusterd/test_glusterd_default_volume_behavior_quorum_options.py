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
    Test Default volume behavior and quorum options
"""

from tests.d_parent_test import DParentTest

# disruptive;dist,rep,arb,dist-rep,disp,dist-arb


class TestCase(DParentTest):

    def _validate_vol_options(self, option_name, option_value, for_all=False):
        """ Function to validate default vol options """
        if not for_all:
            ret = self.redant.get_volume_options(self.vol_name, option_name,
                                                 self.server_list)
        else:
            ret = self.redant.get_volume_options('all', option_name,
                                                 self.server_list)

        value = ret[option_name]
        if value != option_value:
            raise Exception(f"Volume option {option_name} is not equal to "
                            f"{option_value}")

    def _get_total_brick_processes_count(self):
        """
        Function to find the total number of brick processes in the cluster
        """
        count = 0
        brick_list = self.redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
        for brick in brick_list:
            server = brick.split(":")[0]
            count += self.redant.get_brick_processes_count(server)
        return count

    def run_test(self, redant):
        """
        Test default volume behavior and quorum options
        1. Create a volume and start it.
        2. Check that no quorum options are found in vol info.
        3. Kill two glusterd processes.
        4. There shouldn't be any effect to the running glusterfsd
        processes.
        """
        # Check the default quorum options are correct.
        self._validate_vol_options('cluster.server-quorum-type', 'off')
        self._validate_vol_options('cluster.server-quorum-ratio',
                                   '51', True)

        # Get the count of number of glusterfsd processes running.
        count_before_glusterd_kill = self._get_total_brick_processes_count()

        # Kill two glusterd processes.
        servers_list = [self.server_list[1], self.server_list[2]]
        redant.stop_glusterd(servers_list)

        ret = redant.is_glusterd_running(servers_list)
        if ret == 1:
            raise Exception("Glusterd is not stopped on the servers where it"
                            " was desired to be stopped.")

        # Get the count of number of glusterfsd processes running.
        count_after_glusterd_kill = self._get_total_brick_processes_count()

        # The count of glusterfsd processes should match
        if count_before_glusterd_kill != count_after_glusterd_kill:
            raise Exception("Glusterfsd processes are affected.")

        # Start glusterd on all servers.
        redant.start_glusterd(self.server_list)

        # Wait for glusterd to restart.
        ret = redant.wait_for_glusterd_to_start(self.server_list)
        if not ret:
            raise Exception("Glusterd not up on all nodes.")
