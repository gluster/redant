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
    Add tc to check eager lock cli
"""

# nonDisruptive;disp,dist-disp

from random import choice
import string
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):
    @staticmethod
    def get_random_string(chars, str_len=4):
        return ''.join((choice(chars) for _ in range(str_len)))

    def run_test(self, redant):
        """
        Testcase Steps:
        1.Create an EC volume
        2.Set the eager lock option by turning
          on disperse.eager-lock by using different inputs:
          - Try non boolean values(Must fail)
          - Try boolean values
        """
        # Set the eager lock option by turning
        # on disperse.eager-lock by using different inputs
        key = 'disperse.eager-lock'

        # Set eager lock option with non-boolean value
        for char_type in (string.ascii_letters, string.digits):
            temp_val = self.get_random_string(char_type)
            value = f"{temp_val}"
            ret = redant.set_volume_options(self.vol_name, {key: value},
                                            self.server_list[0], excep=False)
            if ret['msg']['opRet'] == '0':
                raise Exception(f"Unexpected: Erroneous {value} to option "
                                "Eagerlock should result in failure")

        # Set eager lock option with boolean value
        for value in ('1', '0', 'off', 'on', 'disable', 'enable'):
            ret = redant.set_volume_options(self.vol_name, {key: value},
                                            self.server_list[0])
