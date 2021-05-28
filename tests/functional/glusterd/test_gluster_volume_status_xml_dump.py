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
    Test Default volume behavior and quorum options
"""


from time import sleep
from tests.nd_parent_test import NdParentTest


# nonDisruptive;dist-arb
class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. stop one of the volume
            (i.e) gluster volume stop <vol-name>
        2. Get the status of the volumes with --xml dump
            XML dump should be consistent
        """

        volume_type1 = 'dist'
        volume_name1 = f"{self.test_name}-{volume_type1}-1"
        redant.volume_create(volume_name1, self.server_list[0],
                             self.vol_type_inf[self.conv_dict[volume_type1]],
                             self.server_list, self.brick_roots, True)
        redant.volume_start(volume_name1, self.server_list[0])
        redant.volume_stop(self.vol_name, self.server_list[0], force=True)
        sleep(2)
        out = redant.get_volume_status(node=self.server_list[0])
        if out is None:
            raise Exception("Failed to get volume status on "
                            f"{self.server_list[0]}")

        for _ in range(4):
            sleep(2)
            out1 = redant.get_volume_status(node=self.server_list[0])
            if out1 is None:
                raise Exception("Failed to get volume status on "
                                f"{self.server_list[0]}")
            if out1 != out:
                raise Exception

        redant.volume_stop(volume_name1, self.server_list[0])
        redant.volume_delete(volume_name1, self.server_list[0])
