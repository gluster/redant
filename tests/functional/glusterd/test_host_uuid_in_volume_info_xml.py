"""
  Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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
"""

from tests.nd_parent_test import NdParentTest


# nonDisruptive;dist-rep
class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        Steps:
        1) Get Volume info
        2) Extract number of bricks
        3) Check for uuid validity for all the bricks.
        """

        # check gluster vol info --xml
        xml_output = redant.get_volume_info(self.server_list[0], self.vol_name)

        # volume info --xml should have non zero UUID for host and brick
        uuid_with_zeros = '00000000-0000-0000-0000-000000000000'
        len_of_uuid = len(uuid_with_zeros)
        number_of_bricks = int(xml_output[self.vol_name]['brickCount'])
        for i in range(number_of_bricks):
            uuid = xml_output[self.vol_name]['bricks'][i]['hostUuid']
            if len(uuid) != len_of_uuid:
                raise Exception("Invalid uuid length")
            if uuid == uuid_with_zeros:
                raise Exception(f"Invalid uuid {uuid}")
