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
      Default max bricks per-process should be 250
"""

from tests.abstract_test import AbstractTest

# disruptive;rep,dist,arb,disp,dist-rep,dist-arb,dist-disp


class TestDefaultMaxBricksPerProcess(AbstractTest):

    def run_test(self, redant):
        """
        Test Case:
        1) Create a volume and start it.
        2) Fetch the max bricks per process value
        3) Reset the volume options
        4) Fetch the max bricks per process value
        5) Compare the value fetched in last step with the initial value
        6) Enable brick-multiplexing in the cluster
        7) Fetch the max bricks per process value
        8) Compare the value fetched in last step with the initial value
        """
        # Fetch the max bricks per process value
        ret = redant.get_volume_options(node=self.server_list[0])
        initial_value = ret['cluster.max-bricks-per-process']

        # Reset the volume options
        redant.reset_volume_option('all', 'all', self.server_list[0])

        # Fetch the max bricks per process value
        redant.validate_volume_option(
            'all', {'cluster.max-bricks-per-process': initial_value},
            self.server_list[0])

        # Enable brick-multiplex in the cluster
        redant.set_volume_options(
            'all', {'cluster.brick-multiplex': 'enable'},
            self.server_list[0])

        redant.validate_volume_option(
            'all', {'cluster.max-bricks-per-process': initial_value},
            self.server_list[0])
