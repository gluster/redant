"""
 Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
    TC to check client IO threads on replicated volume
"""

# disruptive;dist,rep
from tests.d_parent_test import DParentTest


class TestClientIOThreadsOnReplicatedVolumes(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        if self.volume_type == "dist":
            conf_hash = self.vol_type_inf['dist']
            conf_hash['dist_count'] = 1

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)

    def _check_value_of_performance_client_io_threads(self, enabled=True):
        """Check value of performance.client-io-threads"""
        # Setting output value based on enabled param value
        value, instances = "off", 0
        if enabled:
            value, instances = "on", 3

        # Check if output value is same as expected or not
        option = "performance.client-io-threads"
        ret = self.redant.get_volume_options(self.vol_name, option,
                                             self.server_list[0])
        if ret["performance.client-io-threads"] != value:
            raise Exception("Unexpected: performance.client-io-threads value"
                            f" {ret['performance.client-io-threads']} instead"
                            f"of {value}")

        # Check if io-threads is loaded or not based on enabled param value
        filename = (f"/var/lib/glusterd/vols/{self.vol_name}/trusted-"
                    f"{self.vol_name}")
        ret = self.redant.occurences_of_pattern_in_file(self.server_list[0],
                                                        'io-threads',
                                                        filename)
        if ret != instances:
            raise Exception(f"Number of io-threads not equal to {instances}")

    def run_test(self, redant):
        """
        Test case 1:
        1. Create distrubuted volume and start it.
        2. Check the value of performance.client-io-threads it should be ON.
        3. io-threads should be loaded in trusted-.tcp-fuse.vol.
        4. Add brick to convert to replicate volume.
        5. Check the value of performance.client-io-threads it should be OFF.
        6. io-threads shouldn't be loaded in trusted-.tcp-fuse.vol.
        7. Remove brick so thate volume type is back to distributed.
        8. Check the value of performance.client-io-threads it should be ON.
        9. performance.client-io-threads should be loaded in
           trusted-.tcp-fuse.vol.

        Test case 2:
        1. Create a replicate volume and start it.
        2. Set performance.client-io-threads to ON.
        3. Check the value of performance.client-io-threads it should be ON.
        4. io-threads should be loaded in trusted-.tcp-fuse.vol.
        5. Add bricks to convert to make the volume 2x3.
        6. Check the value of performance.client-io-threads it should be ON.
        7. io-threads should be loaded in trusted-.tcp-fuse.vol.
        8. Remove brick to make the volume 1x3 again.
        9. Check the value of performance.client-io-threads it should be ON.
        10. performance.client-io-threads should be loaded in
            trusted-.tcp-fuse.vol.
        """
        # If volume type is distributed then run test case 1.
        if self.volume_type == "dist":
            # Check the value of performance.client-io-threads it should be ON
            # and io-threads should be loaded in trusted-.tcp-fuse.vol
            self._check_value_of_performance_client_io_threads()

            # Add brick to convert to replicate volume
            brick = redant.form_brick_cmd_to_add_brick(self.server_list[0],
                                                       self.vol_name,
                                                       self.server_list,
                                                       self.brick_roots)
            if brick is None:
                raise Exception("Failed to form brick list to add brick")

            redant.add_brick(self.vol_name, brick, self.server_list[0],
                             force=True, replica_count=2)

            # Check the value of performance.client-io-threads it should be ON
            # and io-threads should be loaded in trusted-.tcp-fuse.vol
            self._check_value_of_performance_client_io_threads(enabled=False)

            # Remove brick so thate volume type is back to distributed
            ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                       replica_num=1)
            if not ret:
                raise Exception("Failed to remove-brick from volume")

            # Check the value of performance.client-io-threads it should be ON
            # and io-threads should be loaded in trusted-.tcp-fuse.vol
            self._check_value_of_performance_client_io_threads()

        # If volume type is replicated then run test case 2.
        else:
            # Set performance.client-io-threads to ON
            options = {"performance.client-io-threads": "on"}
            redant.set_volume_options(self.vol_name, options,
                                      self.server_list[0])

            # Check the value of performance.client-io-threads it should be ON
            # and io-threads should be loaded in trusted-.tcp-fuse.vol
            self._check_value_of_performance_client_io_threads()

            # Add bricks to convert to make the volume 2x3
            ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                       self.server_list, self.brick_roots)
            if not ret:
                raise Exception("Failed to add brick on volume "
                                f"{self.vol_name}")

            # Check the value of performance.client-io-threads it should be ON
            # and io-threads should be loaded in trusted-.tcp-fuse.vol
            self._check_value_of_performance_client_io_threads()

            # Remove brick to make the volume 1x3 again
            ret = redant.shrink_volume(self.server_list[0], self.vol_name)
            if not ret:
                raise Exception("Failed to remove-brick from volume")

            # Check the value of performance.client-io-threads it should be ON
            # and io-threads should be loaded in trusted-.tcp-fuse.vol
            self._check_value_of_performance_client_io_threads()
