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
      Test to check that default log level of CLI should be INFO
"""

from tests.abstract_test import AbstractTest

# nonDisruptive;rep


class TestDefaultLogLevelOfCLI(AbstractTest):

    def run_test(self, redant):
        """
        Test Case:
        1) Create and start a volume
        2) Run volume info command
        3) Run volume status command
        4) Run volume stop command
        5) Run volume start command
        6) Check the default log level of main.log
        """
        # Check volume info operation
        redant.get_volume_info(self.server_list[0])

        # Check volume status operation
        redant.get_volume_status(node=self.server_list[0])

        # Check volume stop operation
        redant.volume_stop(
            self.vol_name, self.server_list[0], True)

        # Check volume start operation
        redant.volume_start(self.vol_name, self.server_list[0])

        # Check the default log level of cli.log
        cmd = "ls -tr /tmp/redant/ | tail -1"
        ret = redant.execute_command(cmd, self.server_list[0])
        log_file = ret['msg'][0][:-1]
        cmd = f"cat /tmp/redant/'{log_file}'/main.log | grep -F DEBUG | wc -l"
        ret = redant.execute_command(cmd, self.server_list[0])

        if int(ret['msg'][0].split("\\")[0]) == 0:
            redant.logger.info("The default log level is INFO")
        else:
            redant.logger.info("The default log level is DEBUG")
