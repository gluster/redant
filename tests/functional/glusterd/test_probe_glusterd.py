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
    Test Cases in this module related to peer probe invalid ip,
    non existing ip, non existing host.
"""
# disruptive;

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        '''
        Test script to verify peer probe non existing ip,
        non_exsting_host and invalid-ip, peer probe has to
        be fail for invalid-ip, non-existing-ip and
        non existing host, verify Glusterd services up and
        running or not after invalid peer probe,
        and core file should not get created
        under "/", /var/log/core and /tmp  directory
        '''
        ret = redant.execute_abstract_op_node('date +%s', self.server_list[0])
        test_timestamp = ret['msg'][0].strip()
        # Assigning non existing ip to variable
        non_exist_ip = '256.256.256.256'

        # Assigning invalid ip to variable
        invalid_ip = '10.11.a'

        # Assigning non existing host to variable
        non_exist_host = 'abc.lab.eng.blr.redhat.com'

        # Peer probe checks for non existing host
        try:
            ret = redant.peer_probe(non_exist_host, self.server_list[0])
        except Exception as error:
            redant.logger.info("Peer probe failed for non-existing server")
            redant.logger.info(f"Error: {error}")

        try:
            ret = redant.peer_probe(invalid_ip, self.server_list[0])
        except Exception as error:
            redant.logger.info("Peer probe failed for invalid IP")
            redant.logger.info(f"Error: {error}")

        try:
            ret = redant.peer_probe(non_exist_ip, self.server_list[0])
        except Exception as error:
            redant.logger.info("Peer probe failed for non-existing IP")
            redant.logger.info(f"Error: {error}")

        # Checks Glusterd services running or not after peer probe
        # to invalid host and non existing host

        redant.is_glusterd_running(self.server_list[0])

        # Chekcing core file created or not in "/", "/tmp" and
        # "/var/log/core" directory
        ret = redant.check_core_file_exists(self.server_list, test_timestamp)
        if ret:
            raise Exception('Core file found')
