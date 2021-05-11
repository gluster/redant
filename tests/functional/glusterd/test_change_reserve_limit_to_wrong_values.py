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
    Test changing reserve limit to wrong values
"""

import string
from random import choice
from tests.abstract_test import AbstractTest

# nonDisruptive;dist-rep


class TestChangeReserveLimit(AbstractTest):
    """
    Test to validate behaviour of 'storage.reserve' option on supplying
    erroneous values.
    """
    @staticmethod
    def get_random_string(chars, str_len=4):
        return ''.join((choice(chars) for _ in range(str_len)))

    def run_test(self, redant):
        """
        Test Case:
        1) Create and start a distributed-replicated volume.
        2) Give different inputs to the storage.reserve volume set options
        3) Validate the command behaviour on wrong inputs
        """

        # Creation of random data for storage.reserve volume option
        # Data has: alphabets, numbers, punctuations and their combinations
        key = 'storage.reserve'
        try:
            for char_type in (string.ascii_letters, string.punctuation,
                              string.printable):

                temp_val = self.get_random_string(char_type)
                temp_val = temp_val.replace("'", "").replace("&", "")
                value = "'{}'".format(temp_val)
                redant.set_volume_options(self.vol_name, {key: value},
                                          self.server_list[0])
        except Exception:
            redant.logger.info("Wrong value was tested successfully")

        # Passing an out of range value
        try:
            for value in ('-1%', '-101%', '101%', '-1', '-101'):
                redant.set_volume_options(self.vol_name,
                                          {key: value},
                                          self.server_list[0])
        except Exception:
            redant.logger.info("Wrong value was tested successfully")
