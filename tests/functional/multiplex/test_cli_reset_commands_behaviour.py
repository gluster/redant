"""
Copyright (C) 2019  Red Hat, Inc. <http://www.redhat.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Description:
    Tests for brick multiplexing reset command
"""

# disruptive;rep
from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        1. Set cluster.brick-multiplex to enabled.
        2. Create and start 2 volumes of type 1x3 and 2x3.
        3. Check if cluster.brick-multiplex is enabled.
        4. Reset the cluster using "gluster v reset all".
        5. Check if cluster.brick-multiplex is disabled.
        6. Create a new volume of type 2x3.
        7. Set cluster.brick-multiplex to enabled.
        8. Stop and start all three volumes.
        9. Check the if pids match and check if more
           than one pids of glusterfsd is present.
        """
        # Enable brick multiplexing
        if not redant.is_brick_mux_enabled(self.server_list[0]):
            if not redant.enable_brick_mux(self.server_list[0]):
                raise Exception("Failed to enable brick multiplexing")

        # Create and start 2 volumes of type 1x3 and 2x3
        volume_type_config = {
            'rep': {
                'dist_count': 1,
                'replica_count': 2,
                'transport': 'tcp'},
            'dist-rep': {
                'dist_count': 2,
                'replica_count': 3,
                'transport': 'tcp'}
        }
        for vol_type, conf in volume_type_config.items():
            vol_name = f"vol-{vol_type}"
            redant.setup_volume(vol_name, self.server_list[0],
                                conf, self.server_list,
                                self.brick_roots, force=True)

        # Check if volume option cluster.brick-multiplex is enabled
        volume_list = redant.get_volume_list(self.server_list[0])

        for volume in volume_list:
            option_dict = (redant.get_volume_options(volume,
                           'cluster.brick-multiplex', self.server_list[0]))
            if option_dict['cluster.brick-multiplex'] != 'enable':
                raise Exception("Option brick-multiplex is not enabled")

        # Reset cluster
        redant.reset_volume_option("all", "all", self.server_list[0])

        # Check if brick-multiplex is disabled
        if redant.is_brick_mux_enabled(self.server_list[0]):
            raise Exception("Brick multiplexing status is not disable")

        # Create new distributed-replicated volume
        # Define new 2x3 distributed-replicated volume
        volume_type_config = {
            'dist_count': 2,
            'replica_count': 3,
            'transport': 'tcp'
        }
        vol_name = "new_vol"
        redant.setup_volume(vol_name, self.server_list[0],
                            volume_type_config, self.server_list,
                            self.brick_roots, force=True)

        # Resetting brick-mux back to enabled.
        if not redant.enable_brick_mux(self.server_list[0]):
            raise Exception("Failed to enable brick multiplexing")

        # Restart all volumes
        volume_list = redant.get_volume_list(self.server_list[0])
        for volume in volume_list:
            # Stop the volume
            redant.volume_stop(volume, self.server_list[0])

            # Sleeping for 2 seconds between stop and start.
            sleep(2)

            # Start the volume
            redant.volume_start(volume, self.server_list[0])

        # Check if bricks pid don`t match glusterfsd pid
        for volume in volume_list:
            if not (redant.check_brick_pid_matches_glusterfsd_pid(volume,
                    self.server_list[0])):
                raise Exception("Bricks pid match glusterfsd pid for volume")

        # Checking if the number of glusterfsd is more than one
        for server in self.server_list:
            ret = redant.get_brick_processes_count(server)
            if ret != 1:
                raise Exception("Number of glusterfsd is more than one.")

        # Disable brick multiplexing
        if redant.is_brick_mux_enabled(self.server_list[0]):
            if not redant.disable_brick_mux(self.server_list[0]):
                raise Exception("Failed to disable brick multiplexing")
