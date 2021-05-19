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


Test Description:
Tests to check the 'options' file is updated with quorum changes

"""

from tests.d_parent_test import DParentTest

# disruptive;rep,dist,dist-rep,disp,dist-disp,arb,dist-arb


class TestCase(DParentTest):

    def check_options_file(self, redant, option: str):
        """
        This function checks 'options' file
        for quorum related entries

        Args:
        redant: Redant object

        Returns:
        The message from dictionary ret.
        """
        cmd = f"cat /var/lib/glusterd/options | grep {option}"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        return ret['msg'][0]

    def run_test(self, redant):
        """
        Test Case:
        1. Create and start a volume
        2. Check the output of '/var/lib/glusterd/options' file
        3. Store the value of 'global-option-version'
        4. Set server-quorum-ratio to 70%
        5. Check the output of '/var/lib/glusterd/options' file
        6. Compare the value of 'global-option-version' and check
           if the value of 'server-quorum-ratio' is set to 70%
        """
        # Checking 'options' file for quorum related entries
        ret = self.check_options_file(redant,
                                      "global-option-version")
        out = ret.rstrip('\n')
        prev_global_op_ver = out.split('=')[1]

        # Setting Quorum ratio in percentage
        quorum_perecent = {'cluster.server-quorum-ratio': '70%'}
        redant.set_volume_options('all', quorum_perecent, self.server_list[0])

        # Checking 'options' file for quorum related entries
        ret = self.check_options_file(redant,
                                      "global-option-version")
        out = ret.rstrip('\n')
        new_global_op_ver = out.split('=')[1]

        if int(prev_global_op_ver) + 1 != int(new_global_op_ver):
            raise Exception("Failed:The global-option-version didn't change"
                            " on a volume set operation")

        redant.logger.info("The global-option-version was successfully "
                           " updated in the options file")

        ret = self.check_options_file(redant,
                                      "server-quorum-ratio")
        out = ret.split("%")[0]
        if out != "cluster.server-quorum-ratio=70":
            raise Exception("Server-quorum-ratio is not updated in"
                            " options file")
