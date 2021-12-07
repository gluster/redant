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
    Tests for brick multiplexing statuses
"""

# disruptive;rep

from random import choice
import string
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @staticmethod
    def get_random_string(chars, str_len=4):
        return ''.join((choice(chars) for _ in range(str_len)))

    def set_max_brick_process_to_string(self, key):
        """Set key value to string, should fail"""
        if key == 'cluster.max-bricks-per-process':
            string_options = (string.ascii_letters, string.punctuation)
        elif key == 'cluster.brick-multiplex':
            string_options = (string.ascii_letters, string.punctuation,
                              string.printable, string.digits)

        for char_type in string_options:
            temp_val = self.get_random_string(char_type)
            temp_val = temp_val.replace("'", "").replace("&", "")
            value = "{}".format(temp_val)
            ret = self.redant.set_volume_options('all', {key: value},
                                                 self.server_list[0],
                                                 excep=False)
            if 'opRet' in ret['msg'] and ret['msg']['opRet'] == '0':
                raise Exception("Unexpected: Successfully set wrong value for"
                                " a volume")

    def run_test(self, redant):
        """
        Test case:
        - check if brick multiplex is disable by default
        - check for warning message triggering by setting brick-multiplex and
        choosing 'n' in y/n
        - check if brick multiplex is disabled after triggering warning message
        - check brick multiplex for all possible statuses
        (positive and negative)
        - check for brick multiplex status in /var/lib/glusterd/options file
        """
        # Check if brickmux is disabled by default
        if redant.is_brick_mux_enabled(self.server_list[0]):
            raise Exception("Brick multiplex is not disable by default")

        # Check for warning message while changing status
        warning_message = ("Brick-multiplexing is supported only for "
                           "OCS converged or independent mode. Also it is "
                           "advised to make sure that either all volumes are "
                           "in stopped state or no bricks are running before "
                           "this option is modified."
                           "Do you still want to continue? (y/n)")

        # Checking warning message on enabling multiplex
        cmd = "gluster v set all cluster.brick-multiplex enable"
        ret = redant.execute_command_async(cmd, self.server_list[0])
        ret['stdin'].write("n\n")
        ret = redant.collect_async_result(ret)
        msg = ret['msg'][0]

        if "volume set: success" not in msg:
            if warning_message not in msg:
                raise Exception('There is no warning message in '
                                'output or message is incorrect.')

        else:
            # If brick-mux is enabled then disabling it.
            if redant.is_brick_mux_enabled(self.server_list[0]):
                if not redant.disable_brick_mux(self.server_list[0]):
                    raise Exception("Failed to disable brick multiplexing")

        # Check if brickmux is still disabled
        if redant.is_brick_mux_enabled(self.server_list[0]):
            raise Exception("Brick multiplex is not disable")

        # Enable brick multiplex with all possible statuses
        statuses = ['on', 'enable', '1', 'true',
                    'off', 'disable', '0', 'false']
        for status in statuses:
            cmd = ('yes | gluster v set all cluster.brick-multiplex '
                   f'{status}')
            ret = redant.execute_abstract_op_node(cmd, self.server_list[0],
                                                  False)
            if ret['error_code'] != 0:
                raise Exception("Failed to enable brick multiplex "
                                f"with value {status}")

            # Check if brick multiplex status is correct
            gluster_status = redant.get_brick_mux_status(self.server_list[0])
            if status != gluster_status:
                raise Exception("Brick multiplex status is not correct")

            # Check for brick multiplexing status in file 'options'
            search_pattern = f'cluster.brick-multiplex={status}'
            if not (redant.search_pattern_in_file(self.server_list[0],
                                                  search_pattern,
                                                  '/var/lib/glusterd/options',
                                                  '', '')):
                raise Exception(f"Brick multiplexing status {status} in file "
                                "'/var/lib/glusterd/options' is incorrect")

        # Check brick multiplex with incorrect status
        cmd = ("yes | gluster v set all cluster.brick-multiplex incorrect")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0],
                                              False)
        if ret['error_code'] == 0:
            raise Exception("Successfully enabled brick multiplex "
                            "with value incorrect")

        """
        test_enabling_brick_mux_with_wrong_values
        Test Case:
        - Create a gluster cluster
        - Set cluster.brick-multiplex value to random string(Must fail)
        - Set cluster.brick-multiplex value to random int(Must fail)
        - Set cluster.brick-multiplex value to random
          special characters(Must fail)
        """
        # Creation of random data for cluster.brick-multiplex option
        # Data has: alphabets, numbers, punctuations and their combinations
        key = 'cluster.brick-multiplex'
        self.set_max_brick_process_to_string(key)

        """
        test_enable_brick_mux_with_max_bricks_per_process
        Test Case:
        - Create a gluster cluster
        - With brick mux set to disable:
            1.Set cluster.max-bricks-per-process to int and check
              error message(Must fail)
            2.Set cluster.max-bricks-per-process to string(Must fail)
        - With brick mux set to enable:
            1.Set cluster.max-bricks-per-process to string(Must fail)
            2.Set cluster.max-bricks-per-process to 0
            3.Set cluster.max-bricks-per-process to 1 and check
              error message.(Must fail)
            4.Set cluster.max-bricks-per-process to int value > 1.
        """
        # Disabling cluster.brick-multiplex if not.
        if redant.is_brick_mux_enabled(self.server_list[0]):
            if not redant.disable_brick_mux(self.server_list[0]):
                raise Exception("Failed to disable brick multiplexing")

        # Set cluster.max-bricks-per-process to int and check
        # error message(Must fail)
        cmd = "gluster v set all cluster.max-bricks-per-process 10"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception('Unexpected: Able to set max-bricks-per-process'
                            'without enabling brick mux')
        err_msg = ("volume set: failed: Brick-multiplexing is not enabled. "
                   "Please enable brick multiplexing before trying to set "
                   "this option.")
        if err_msg not in ret['error_msg']:
            raise Exception("Error message not proper on trying to "
                            "set max-bricks-per-process without brickmux")

        # Set cluster.max-bricks-per-process to string(Must fail)
        key = 'cluster.max-bricks-per-process'
        self.set_max_brick_process_to_string(key)

        # Enable cluster.brick-multiplex.
        if not redant.enable_brick_mux(self.server_list[0]):
            raise Exception("Failed to enable brick multiplexing")

        # Set cluster.max-bricks-per-process to string(Must fail)
        key = 'cluster.max-bricks-per-process'
        self.set_max_brick_process_to_string(key)

        # Set cluster.max-bricks-per-process to 0.
        redant.set_volume_options('all',
                                  {'cluster.max-bricks-per-process': '0'},
                                  self.server_list[0])

        # Set cluster.max-bricks-per-process to 1 and check
        # error message.(Must fail)
        cmd = "gluster v set all cluster.max-bricks-per-process 1"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception('Able to set max-bricks-per-process to 1,'
                            'after enabling brick mux')
        err_msg = ("volume set: failed: Brick-multiplexing is enabled."
                   " Please set this option to a value other than 1 to"
                   " make use of the brick-multiplexing feature.")
        if err_msg not in ret['error_msg']:
            raise Exception("Error message not proper on trying to set "
                            "max-bricks-per-process with brickmux")

        # Set cluster.max-bricks-per-process to int value > 1
        key = 'cluster.max-bricks-per-process'
        temp_val = self.get_random_string(string.digits)
        value = "{}".format(temp_val)
        redant.set_volume_options('all', {key: value}, self.server_list[0])

        # Disable brick multiplexing
        if not redant.disable_brick_mux(self.server_list[0]):
            raise Exception("Failed to disable brick multiplexing")
