"""
  Copyright (C) 2019-2020  Red Hat, Inc. <http://www.redhat.com>

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
  Test case to check local time logging and op-version
"""

# disruptive;dist
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Skip if RHGS installation
        self.redant.check_gluster_installation(self.server_list, "upstream")

        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)

    def _logging_time_check(self):
        """
        Check if the logging is done in localtime
        """
        cmd = ("cat /var/log/glusterfs/glusterd.log | tail -n 2 | head -n 1"
               " | grep $(date +%H:%M) | wc -l")
        ret = self.redant.execute_abstract_op_node(cmd, self.server_list[0])
        return int(ret['msg'][0].rstrip('\n'))

    def run_test(self, redant):
        """
        Test steps:
        1. Enable localtime time for the cluster
        2. Disable the localtime logging option
        3. Check invalid transport type value
        4. Set op-version for a volume, it should fail
        5. Set multiple options along with localtime logging option
        6. Set incompatible max, current op-version
        """

        # Enable localtime logging
        option_val = {'localtime-logging': 'enable'}
        redant.set_volume_options('all', option_val, self.server_list[0])
        ret = self._logging_time_check()
        if ret == 0:
            raise Exception("Failed to enable localtime logging option in"
                            " cluster")

        # Disable localtime logging
        option_val = {'localtime-logging': 'disable'}
        redant.set_volume_options('all', option_val, self.server_list[0])
        ret = self._logging_time_check()
        if ret != 0:
            raise Exception("Failed to disable localtime logging option in"
                            " cluster")

        # Set invalid value for transport type, should fail
        option_val = {'config.transport': 'rcp'}
        ret = redant.set_volume_options(self.vol_name, option_val,
                                        self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully set invalid "
                            "config.transport option for volume")

        # Set op-version for a volume should fail
        option_val = {'cluster.op-version': '80000'}
        ret = redant.set_volume_options(self.vol_name, option_val,
                                        self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully set op-version "
                            "option for a volume")

        # Setting op-version and localtime logging together, should fail
        option_val = {'cluster.op-version': '80000',
                      'localtime-logging': 'enable'}
        ret = redant.set_volume_options('all', option_val,
                                        self.server_list[0], True, False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully set another "
                            "option with op-version")

        # Set invalid op-version, should fail
        option_val = {'cluster.op-version': '80-000'}
        ret = redant.set_volume_options('all', option_val,
                                        self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully set invalid "
                            "op-version option for a volume")

        # Get maximum op-version
        ret = redant.get_volume_options('all', 'cluster.max-op-version',
                                        self.server_list[0])
        max_op_version = int(ret['cluster.max-op-version'])

        # Set op-version greater than the allowed op-version
        new_op_version = max_op_version + 1000
        option_val = {'cluster.op-version': new_op_version}
        ret = redant.set_volume_options('all', option_val,
                                        self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully set op-version "
                            "greater than the max-op-version option for the"
                            " cluster")

        # Get current op-version
        ret = redant.get_volume_options('all', 'cluster.op-version',
                                        self.server_list[0])
        curr_op_version = int(ret['cluster.op-version'])

        # Set op-version lesser than the current op-version
        new_op_version = curr_op_version - 1000
        option_val = {'cluster.op-version': new_op_version}
        ret = redant.set_volume_options('all', option_val,
                                        self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully set op-version "
                            "lesser than the current-op-version option for"
                            " the cluster")
