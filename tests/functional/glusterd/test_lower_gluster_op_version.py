"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
        Test Cases in this module related to setting
        valid and invalid op-version values.
"""

# nonDisruptive;rep
from tests.abstract_test import AbstractTest


class LowerGlusterOpVersion(AbstractTest):

    def run_test(self, redant):
        """
        - Create volume
        - Get the volume op-version
        - Set the valid lower op-version
        - Set the invalid op-version
        """
        # Get the volume op-version
        ret = (redant.
               get_volume_options(node=self.server_list[0])
               ['cluster.op-version'])
        redant.logger.info(f"Op-verion: {ret}")
        redant.logger.info("Successfully got the op-version")

        # Lowest opversion is 30000
        lowest_op_version = 30000
        invalid_op_version = "abc"
        lower_op_version_dict = {'cluster.op-version': lowest_op_version}
        invalid_op_version_dict = {'cluster.op-version': invalid_op_version}

        # Set the volume option with lower op-version
        try:
            redant.set_volume_options('all', lower_op_version_dict,
                                      self.server_list[0])
        except Exception as error:
            redant.logger.info(error)
            redant.logger.info("Failed: setting lower"
                               " op-version.")

        # Setting invalid opversion
        try:
            redant.set_volume_options('all', invalid_op_version_dict,
                                      self.server_list[0])
        except Exception as error:
            redant.logger.info(error)
            redant.logger.info("Successfully tested setting invalid"
                               " op-version.")
