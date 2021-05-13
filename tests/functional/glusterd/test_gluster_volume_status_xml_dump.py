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

# nonDisruptive;dist-arb
from time import sleep
from tests.abstract_test import AbstractTest


class GetVolumeStatusXmlDump(AbstractTest):

    def run_test(self, redant):
        """
        Setps:
        1. stop one of the volume
            (i.e) gluster volume stop <vol-name>
        2. Get the status of the volumes with --xml dump
            XML dump should be consistent
        """
        redant.volume_stop(self.vol_name, self.server_list[0], force=True)
        out = redant.get_volume_status(self.mnode)
        if out is None:
            redant.logger.error("Failed to get volume status on "
                                f"{self.server_list[0]}")

        for _ in range(4):
            sleep(2)
            out1 = redant.get_volume_status(self.mnode)
            if out1 is None:
                redant.logger.error("Failed to get volume status on "
                                    f"{self.server_list[0]}")
            self.assertEqual(out1, out)
