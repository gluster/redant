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

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    This module tries to create and validate EC volume
    with various combinations of input parameters.
"""

# disruptive;disp,dist-disp
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestEcValidateVolumeCreate(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        # Check server requirements
        self.redant.check_hardware_requirements(self.server_list, 6)

    def run_test(self, redant):
        """
        Steps:
        - Verify volume creation should fail in case of insufficient bricks
        - Repeat the above step wit force option, and it should pass
        - Verify volume creation with valid config
        - Verify volume creation with different invalid combinations of
          disperse and redundancy count
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])

        # Test 1: Verify volume creation with insufficient bricks
        # Setup input parameters
        conf_hash['redundancy_count'] = 2
        conf_hash['disperse_count'] = 6

        # Restrict the brick servers to data brick count
        data_brick_count = (conf_hash['disperse_count']
                            - conf_hash['redundancy_count'])

        # Setup Volume without force
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash,
                                  self.server_list[0:data_brick_count],
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name}")

        # Setup Volume with force
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash,
                                  self.server_list[0:data_brick_count],
                                  self.brick_roots, force=True, excep=False)
        if ret['error_code'] != 0:
            raise Exception("Unexpected: Volume setup is failing "
                            f"for volume {self.vol_name} with force")

        # Stopping the volume
        ret = redant.cleanup_volume(self.server_list[0], self.vol_name)
        if not ret:
            raise Exception("Failed to cleanup Volume")

        # Test 2: Test cases to verify valid input combinations.

        # Setup Volume and Mount Volume
        redant.setup_volume(self.vol_name, self.server_list[0],
                            conf_hash, self.server_list,
                            self.brick_roots)

        # Stopping the volume
        ret = redant.cleanup_volume(self.server_list[0], self.vol_name)
        if not ret:
            raise Exception("Failed to cleanup Volume")

        # Test 3: Test cases to verify invalid input combinations.
        # Setup input parameters
        conf_hash['redundancy_count'] = 2
        conf_hash['disperse_count'] = 6

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")

        # Usecase 2: Increase the redundancy count
        conf_hash['redundancy_count'] = 3

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")

        # Usecase 3: Increase the redundancy count
        conf_hash['redundancy_count'] = 4

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")

        # Usecase 4: Increase the redundancy count
        conf_hash['redundancy_count'] = 6

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")

        # Usecase 5: Invalid disperse and redundancy count combination
        conf_hash['redundancy_count'] = 4
        conf_hash['disperse_count'] = 4

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")

        # Usecase 6: Negative redundancy count
        conf_hash['redundancy_count'] = -2
        conf_hash['disperse_count'] = 6

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")

        # Usecase 7: Negative redundancy, disperse count
        conf_hash['redundancy_count'] = -2
        conf_hash['disperse_count'] = -4

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")

        # Usecase 6: Negative disperse count
        conf_hash['redundancy_count'] = 2
        conf_hash['disperse_count'] = -4

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")

        # Usecase 6: Zero disperse count
        conf_hash['redundancy_count'] = 2
        conf_hash['disperse_count'] = 0

        # Setup Volume, it should fail
        ret = redant.setup_volume(self.vol_name, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Volume setup is not failing "
                            f"for volume {self.vol_name} with invalid input")
