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
    Test Cases in this module tests Gluster against SELinux Labels and Policies
"""
# nonDisruptive;
from tests.abstract_test import AbstractTest


class TestGlusterAgainstSELinux(AbstractTest):

    @staticmethod
    def get_cmd(cmd, opts='', operate_on=''):
        if opts:
            opts = '-'+opts
        command = f"{cmd} {opts} {operate_on}"
        return command

    def run_test(self, redant):
        """
        TestCase:
        1. Check the existence of '/usr/lib/firewalld/services/glusterfs.xml'
        2. Validate the owner of this file as 'glusterfs-server'
        3. Validate SELinux label context as 'system_u:object_r:lib_t:s0'
        """

        fqpath = '/usr/lib/firewalld/services/glusterfs.xml'

        for server in self.server_list:
            # Check existence of xml file
            if not redant.path_exists(server, fqpath):
                redant.logger.error("Failed to verify existence of"
                                    f"'{fqpath}' in {server} ")
                continue

            # Check owner of xml file
            command = self.get_cmd('rpm', 'qf', fqpath)
            ret = redant.execute_io_cmd(command, server)
            exp_str = 'glusterfs-server'
            ret_msg = " ".join(ret['msg'])
            if exp_str not in ret_msg:
                redant.logger.error(f"Fail: Owner of {fqpath} should be "
                                    f"{exp_str} on {server}")

            # Validate SELinux label
            command = self.get_cmd('ls', 'lZ', fqpath)
            ret = redant.execute_io_cmd(command, server)
            exp_str = 'system_u:object_r:lib_t:s0'
            if exp_str not in ret_msg:
                redant.logger.error(f"Fail: SELinux label on {fqpath}"
                                    f"should be {exp_str} on {server}")
