"""
  Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
  Checks for setting of volution of with lesser and greater than
  4096 characters.
"""

from tests.d_parent_test import DParentTest


# disruptive;dist
class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Skip test if not RHGS installation
        self.redant.check_gluster_installation(self.server_list, "downstream")

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 self.vol_type_inf[self.volume_type],
                                 self.server_list, self.brick_roots,
                                 force=True)

    def run_test(self, redant):
        """
        Steps:
        1. Make a string of <4096 characters.
        2. Set volume option for auth.allow with <4096 characters.
        3. Restart glusterd.
        4. Make a string of >4096 characters.
        5. set volume option for auth.allow with >4096 characsters.
        6. Restart glusterd
        """

        auth_list = []
        for ip_addr in range(256):
            auth_list.append(f'192.168.122.{ip_addr}')
        for ip_addr in range(7):
            auth_list.append(f'192.168.123.{ip_addr}')
        ip_list = ','.join(auth_list)

        # set auth.allow with <4096 characters and restart the glusterd
        redant.logger.info("Setting auth.allow with string of length "
                           f"{len(ip_list)} for {self.vol_name}")
        self.options = {"auth.allow": ip_list}
        redant.set_volume_options(self.vol_name, self.options,
                                  self.server_list[0])
        redant.restart_glusterd(self.server_list[0])

        # wait for glusterd to start
        if not redant.wait_for_glusterd_to_start(self.server_list[0]):
            raise Exception("glusterd is not running on"
                            f"{self.server_list}")

        # set auth.allow with >4096 characters and restart the glusterd
        ip_list = ip_list + ",192.168.123.7"
        self.options = {"auth.allow": ip_list}
        redant.logger.info("Setting auth.allow with string of length "
                           f"{len(ip_list)} for {self.vol_name}")

        redant.set_volume_options(self.vol_name, self.options,
                                  self.server_list[0])

        redant.restart_glusterd(self.server_list[0])

        if not redant.wait_for_glusterd_to_start(self.server_list[0]):
            raise Exception("glusterd is not running on"
                            f"{self.server_list}")
