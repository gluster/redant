"""
 Copyright (C) 2018  Red Hat, Inc. <http://www.redhat.com>

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
    Tests bricks EC version on a EC vol
    Don't send final version update if non data fop succeeded validation
"""

# nonDisruptive;disp
from tests.nd_parent_test import NdParentTest


class TestEcVersion(NdParentTest):

    def run_test(self, redant):
        """
        Steps:
        - Get the brick list for the volume
        - Create a dir 'dir1' on mountpoint
        - Get the EC version of the directory
        - Update permission of the directory
        - Again update permissions
        - Get the EC version of the directory
        - Compare EC version before and after non data FOP, should be equal
        """
        # Get the bricks from the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if not bricks_list:
            raise Exception("Failed to get the brick list")

        # Creating dir1 on the mountpoint
        redant.create_dir(self.mountpoint, "dir1", self.client_list[0])

        ec_version_before_nonfops = []
        ec_version_after_nonfops = []
        # Getting the EC version of the directory
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            target_file = f"{brick_path}/dir1"
            dir_attribute = redant.get_extended_attributes_info(brick_node,
                                                                target_file)
            if not dir_attribute:
                raise Exception("Failed to get extended attributes")

            ec_vers = dir_attribute[target_file]['trusted.ec.version']
            ec_version_before_nonfops.append(ec_vers)

        # chmod of dir1 once
        cmd = f"chmod 777 {self.mountpoint}/dir1"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # chmod of dir1 twice
        cmd = f"chmod 777 {self.mountpoint}/dir1"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Getting the EC version of the directory
        # After changing mode of the directory
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            target_file = f"{brick_path}/dir1"
            dir_attribute = redant.get_extended_attributes_info(brick_node,
                                                                target_file)
            if not dir_attribute:
                raise Exception("Failed to get extended attributes")

            ec_vers = dir_attribute[target_file]['trusted.ec.version']
            ec_version_after_nonfops.append(ec_vers)

        # Comparing the EC version before and after non data FOP
        if ec_version_before_nonfops != ec_version_after_nonfops:
            raise Exception("EC version updated for non data FOP")
