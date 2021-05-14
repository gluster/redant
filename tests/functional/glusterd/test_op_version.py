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
      Test for setting up the max supported op-version and
      verifying  version number in info file
"""

# nonDisruptive;dist-rep
from tests.abstract_test import AbstractTest


class TestMaxSupportedOpVersion(AbstractTest):

    def run_test(self, redant):
        '''
        -> Create Volume
        -> Get the current op-version
        -> Get the max supported op-version
        -> Verify vol info file exists or not in all servers
        -> Get the version number from vol info file
        -> If current op-version is less than max-op-version
        set the current op-version to max-op-version
        -> After vol set operation verify that version number
        increased by one or not in vol info file
        -> verify that current-op-version and max-op-version same or not.
        '''

        # Getting current op-version
        ret = redant.get_volume_options(node=self.server_list[0])
        current_op_version = int(ret['cluster.op-version'])

        # Getting Max op-verison
        max_op_version = int(ret['cluster.max-op-version'])

        # File_path: path for vol info file
        # Checking vol file exist in all servers or not
        file_path = '/var/lib/glusterd/vols/' + self.vol_name + '/info'
        if not redant.path_exists(self.server_list, file_path):
            raise Exception("File does not exist")

        # Getting version number from vol info file
        # cmd: grepping  version from vol info file
        file_path_cmd = ' '.join(['grep', "'^version'", file_path])
        ret = redant.execute_command(file_path_cmd, self.server_list[0])
        version_list = ret['msg'][0].split('=')
        version_no = int(version_list[1]) + 1

        # Comparing current op-version and max op-version
        if current_op_version < max_op_version:

            # Set max-op-version
            ret = redant.set_volume_options(
                'all', {'cluster.op-version': max_op_version},
                self.server_list[0])

            # Grepping version number from vol info file after
            # vol set operation
            ret = redant.execute_command(file_path_cmd,
                                         self.server_list[0])
            version_list = ret['msg'][0].split('=')
            after_version_no = int(version_list[1])

            # Comparing version number before and after vol set operations
            if version_no != after_version_no:
                raise Exception(
                    "After volume set operation version "
                    "number not increased by one"
                )
            # Getting current op-version
            ret = redant.get_volume_options(node=self.server_list[0])
            current_op_version = int(ret['cluster.op-version'])

        # Checking current-op-version and max-op-version equal or not
        elif current_op_version == max_op_version:
            redant.logger.info("Current op-version and max"
                               " op-version are same")
