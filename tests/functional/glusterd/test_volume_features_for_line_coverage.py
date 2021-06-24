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
    TC to check few volume features and line coverage
"""

from tests.d_parent_test import DParentTest

# disruptive;dist


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test Case:
        1) Create and start a volume
        2) Test ganesha options
        3) Test bitrot feature
        4) Test fms log option
        5) Test volume get individual option
        6) Test statedump generation
        7) Test a negative replace brick case
        """
        # Test ganesha option with invalid value
        ganesha_option = {"ganesha.enable": "invalid-value"}
        ret = redant.set_volume_options(self.vol_name, ganesha_option,
                                        self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully enabled ganesha with"
                            " invalid value on volume")

        # Try enable ganesha
        ganesha_option = {"ganesha.enable": "enable"}
        ret = redant.set_volume_options(self.vol_name, ganesha_option,
                                        self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully enabled ganesha on the"
                            " volume")

        # Disable bitrot without enabling
        ret = redant.disable_bitrot(self.vol_name, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Successfully disabled bitrot"
                            " without enabling")

        # Stop the volume
        redant.volume_stop(self.vol_name, self.server_list[0])

        # Try enabling bitrot for stopped volume, should fail
        ret = redant.enable_bitrot(self.vol_name, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Successfully enabled bitrot"
                            " for stopped volume")

        # Start the volume
        redant.volume_start(self.vol_name, self.server_list[0])

        # Enable bitrot
        redant.enable_bitrot(self.vol_name, self.server_list[0])

        # Disable bitrot
        redant.disable_bitrot(self.vol_name, self.server_list[0])

        # Try setting gfproxyd with invalid value for a volume
        ganesha_option = {"onfig.gfproxyd": "invalid-value"}
        ret = redant.set_volume_options(self.vol_name, ganesha_option,
                                        self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully set invalid value "
                            "for gfproxyd")

        # Setting fsm log for localhost should fail
        cmd = "gluster system:: fsm log localhost"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Successfully set fsm log for "
                            " localhost")

        # Get few individual options
        ret = redant.get_volume_options("volume", 'all', self.server_list[0],
                                        False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Successfully fetched all options "
                            "for non-existing volume")

        redant.get_volume_options(self.vol_name, 'config.memory-accounting',
                                  self.server_list[0])
        redant.get_volume_options(self.vol_name, 'config.transport',
                                  self.server_list[0])

        # Generate statedump of glusterd process
        cmd = "pgrep glusterd"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        pid = ret['msg'][0].rstrip('\n')

        cmd = f"rm -rf /var/run/gluster/*.dump*; kill -USR1 {pid}"
        redant.execute_abstract_op_node(cmd, self.server_list[0])

        cmd = ("ls -l /var/run/gluster/ | grep 'glusterdump' | wc -l")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        if ret['msg'][0].rstrip('\n') != '1':
            raise Exception("Failed to generate statedump for glusterd"
                            " process")

        # Replace brick with itself should fail
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get the brick list")

        ret = redant.replace_brick(self.server_list[0], self.vol_name,
                                   brick_list[0], brick_list[0], False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Replace brick was successfull when"
                            " src brick and dst brick was same")
