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
    Tests to check by default ping timer is disabled and epoll
    thread count is 1
"""

from tests.abstract_test import AbstractTest

# nonDisruptive;rep,dist,arb,disp,dist-rep,dist-arb,dist-disp


class TestPingTimerAndEpollThreadCountDefaultValue(AbstractTest):

    def run_test(self, redant):
        """
        Test Steps:
        1. Start glusterd
        2. Check ping timeout value in glusterd.vol should be 0
        3. Create a test script for epoll thread count
        4. Source the test script
        5. Fetch the pid of glusterd
        6. Check epoll thread count of glusterd should be 1
        """
        # Fetch the ping timeout value from glusterd.vol file
        cmd = "cat /usr/local/etc/glusterfs/glusterd.vol |\
               grep -i ping-timeout"

        ret = redant.execute_command(cmd, self.server_list[0])
        out = ret['msg'][0]
        ping_value = out.split("ping-timeout")[1].split('\\')[0]

        # Check if the default value is 0
        if int(ping_value) != 0:
            raise Exception("Unexpected: Default"
                            " value of ping-timeout is not 0")

        # Shell Script to be run for epoll thread count
        script = """
            #!/bin/bash
            function nepoll ()
            {
                local pid=$1;
                for i in $(ls /proc/$pid/task);
                do
                    cat /proc/$pid/task/$i/stack | grep -i 'sys_epoll_wait';
                done
            }
        """

        # Execute the shell script
        cmd = f"echo '{script}' > test.sh;"
        redant.execute_command(cmd, self.server_list[0])
        # Fetch the pid of glusterd
        cmd = "pidof glusterd"
        ret = redant.execute_command(cmd,
                                     self.server_list[0])
        pidof_glusterd = int(ret['msg'][0])

        # Check the epoll thread count of glusterd
        cmd = "source test.sh; nepoll %d | wc -l" % pidof_glusterd
        ret = redant.execute_command(cmd, self.server_list[0])

        count = int(ret['msg'][0])
        if count != 1:
            raise Exception("Unexpected: Default epoll thread"
                            "count is not 1")

        cmd = "rm -f test.sh;"
        redant.execute_command(cmd, self.server_list[0])
