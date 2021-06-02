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
   Test Cases in this module related to Glusterd peer detach.
"""

from tests.d_parent_test import DParentTest

# disruptive;


class TestCase(DParentTest):

    def _check_detach_error_message(self, use_force=True):
        """
        Check detach peer when volume exists
        """
        ret = self.redant.peer_detach(self.server_list[1],
                                      self.server_list[0],
                                      use_force, False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"Server detach should have failed: "
                            f"{self.server_list[1]}")
        err_msg = (f"Peer {self.server_list[1]} hosts one or more bricks."
                   " If the peer is in not recoverable state then use either"
                   " replace-brick or remove-brick command with force to"
                   " remove all bricks from the peer and attempt the peer"
                   " detach again.")
        if err_msg not in ret['msg']['opErrstr']:
            raise Exception("Peer detach didn't fail with proper error msg")

    def run_test(self, redant):
        """
        - peer Detaching specified server from cluster
        - peer Detaching detached server again and checking the error msg
        - peer Detaching invalid host
        - peer Detaching Non exist host
        - peer Checking Core file created or not
        - Peer detach one node which contains the bricks of volume created
        - Peer detach force a node which is hosting bricks of a volume
        - Peer detach one node which hosts bricks of offline volume
        - Peer detach force a node which hosts bricks of offline volume
        """

        # Timestamp of current test case of start time
        ret = redant.execute_abstract_op_node('date +%s', self.server_list[0])
        test_timestamp = ret['msg'][0].rstrip('\n')

        # Assigning non existing host to variable
        self.non_exist_host = '256.256.256.256'

        # Assigning invalid ip to variable
        self.invalid_ip = '10.11.a'

        # Peer detach to specified server
        redant.peer_detach(self.server_list[1], self.server_list[0])

        # Detached server detaching again, Expected to fail detach
        ret = redant.peer_detach(self.server_list[1], self.server_list[0],
                                 False, False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"Server detach should have failed: "
                            f"{self.server_list[1]}")
        err_msg = (f"{self.server_list[1]} is not part of cluster")
        if err_msg not in ret['msg']['opErrstr']:
            raise Exception("Peer detach didn't fail as expected")

        # Probing detached server
        redant.peer_probe(self.server_list[1], self.server_list[0])

        # Detach invalid host
        ret = redant.peer_detach(self.invalid_ip, self.server_list[0],
                                 False, False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"Server detach invalid host should have "
                            f"failed: {self.invalid_ip}")

        # Detach non exist host
        ret = redant.peer_detach(self.non_exist_host, self.server_list[0],
                                 False, False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"Server detach non exist host should have "
                            f"failed: {self.non_exist_host}")

        # Creating Volume
        volume_type = 'dist'
        self.volume_name = f"{self.test_name}-{volume_type}-1"
        redant.setup_volume(self.volume_name, self.server_list[0],
                            self.vol_type_inf[self.conv_dict[volume_type]],
                            self.server_list, self.brick_roots)

        # Peer detach one node which contains the bricks of the volume created
        self._check_detach_error_message(False)

        #  Peer detach force a node which is hosting bricks of a volume
        self._check_detach_error_message()

        # Peer detach one node which contains bricks of an offline volume
        redant.volume_stop(self.volume_name, self.server_list[0])

        self._check_detach_error_message(use_force=False)

        # Forceful Peer detach node which hosts bricks of offline volume
        self._check_detach_error_message()

        # starting volume for proper cleanup
        redant.volume_start(self.volume_name, self.server_list[0])

        # Checking core. file created or not in "/", "/tmp", "/log/var/core
        # directory
        ret = redant.check_core_file_exists(self.server_list, test_timestamp)
        if ret:
            raise Exception("glusterd service should not have crashed")
