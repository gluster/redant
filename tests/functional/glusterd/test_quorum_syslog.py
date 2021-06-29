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

 Description:
   TC to check quorum syslog

TODO: This TC doesn't work on Fedora OS, OPs for OS check needs to be added.
"""

import traceback
from time import sleep
import re
from tests.d_parent_test import DParentTest

# disruptive;dist,rep,dist-rep,disp,dist-disp


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway and one of the nodes has
        glusterd stopped then the glusterd is started on that node
        and then the terminate function in the DParentTest is called
        """
        try:
            self.redant.start_glusterd(self.server_list[1])

            # In this test case performing quorum operations,
            # deleting volumes immediately after glusterd services start,
            # volume deletions are failing with quorum not met,
            # that's the reason verifying peers are connected or not before
            # deleting volumes
            ret = self.redant.wait_till_all_peers_connected(self.server_list)
            if not ret:
                raise Exception("Servers are not in peer probed state")

            # stopping the volume and Cleaning up the volume
            self.redant.cleanup_volume(self.volume_name1, self.server_list[0])

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)

        super().terminate()

    def run_test(self, redant):
        """
        create two volumes
        Set server quorum to both the volumes
        set server quorum ratio 90%
        stop glusterd service any one of the node
        quorum regain message should be recorded with message id - 106002
        for both the volumes in /var/log/messages and
        /var/log/glusterfs/glusterd.log
        start the glusterd service of same node
        quorum regain message should be recorded with message id - 106003
        for both the volumes in /var/log/messages and
        /var/log/glusterfs/glusterd.log
        """

        self.log_messages = "/var/log/messages"
        self.log_glusterd = "/var/log/glusterfs/glusterd.log"

        # Create and start another volume
        volume_type1 = 'dist'
        self.volume_name1 = f"{self.test_name}-{volume_type1}-1"
        redant.setup_volume(self.volume_name1, self.server_list[0],
                            self.vol_type_inf[volume_type1],
                            self.server_list, self.brick_roots)

        # Enabling server quorum all volumes
        self.quorum_options = {'cluster.server-quorum-type': 'server'}
        self.volume_list = redant.get_volume_list(self.server_list[0])
        for volume in self.volume_list:
            redant.set_volume_options(volume, self.quorum_options,
                                      self.server_list[0])

        # Setting Quorum ratio in percentage
        self.quorum_perecent = {'cluster.server-quorum-ratio': '91%'}
        redant.set_volume_options('all', self.quorum_perecent,
                                  self.server_list[0])

        # counting quorum regain messages-id '106002' in  /var/log/messages
        # file, before glusterd services stop
        cmd_messages = f"grep -o '106002' {self.log_messages} | wc -l"
        ret = redant.execute_abstract_op_node(cmd_messages,
                                              self.server_list[0])
        before_glusterd_stop_msgid_count = ret['msg'][0].rstrip('\n')

        # counting quorum regain messages-id '106002' in
        # /var/log/glusterfs/glusterd.log file, before glusterd services stop
        cmd_glusterd = f"grep -o '106002' {self.log_glusterd} | wc -l"
        ret = redant.execute_abstract_op_node(cmd_glusterd,
                                              self.server_list[0])
        before_glusterd_stop_glusterd_id_count = ret['msg'][0].rstrip('\n')

        # Stopping glusterd services
        redant.stop_glusterd(self.server_list[1])

        # checking glusterd service stopped or not
        ret = redant.is_glusterd_running(self.server_list[1])
        if ret != 0:
            raise Exception("Glusterd service is not stopped")

        # counting quorum regain messages-id '106002' in /var/log/messages file
        # after glusterd services stop.
        count = 0
        msg_count = False
        expected_msg_id_count = int(before_glusterd_stop_msgid_count) + 2
        while count <= 10:
            ret = redant.execute_abstract_op_node(cmd_messages,
                                                  self.server_list[0])
            after_glusterd_stop_msgid_count = ret['msg'][0].rstrip('\n')
            if(re.search(r'\b' + str(expected_msg_id_count) + r'\b',
                         after_glusterd_stop_msgid_count)):
                msg_count = True
                break
            sleep(2)
            count += 1

        if not msg_count:
            raise Exception(f"Failed to grep quorum regain message-id "
                            f"106002 count in :{self.log_messages}")

        # counting quorum regain messages-id '106002' in
        # /var/log/glusterfs/glusterd.log file after glusterd services stop
        ret = redant.execute_abstract_op_node(cmd_glusterd,
                                              self.server_list[0])
        after_glusterd_stop_glusterd_id_count = ret['msg'][0].rstrip('\n')

        # Finding quorum regain message-id count difference between before
        # and after glusterd services stop in /var/log/messages
        count_diff = (int(after_glusterd_stop_msgid_count)
                      - int(before_glusterd_stop_msgid_count))

        if count_diff != 2:
            raise Exception(f"Failed to record regain messages "
                            f"in : {self.log_messages}")

        # Finding quorum regain message-id  count difference between before
        # and after glusterd services stop in /var/log/glusterfs/glusterd.log
        count_diff = (int(after_glusterd_stop_glusterd_id_count)
                      - int(before_glusterd_stop_glusterd_id_count))

        # counting quorum messages-id '106003' in a /var/log/messages file
        # before glusterd services start
        cmd_messages = f"grep -o '106003' {self.log_messages} | wc -l"
        ret = redant.execute_abstract_op_node(cmd_messages,
                                              self.server_list[0])
        before_glusterd_start_msgid_count = ret['msg'][0].rstrip('\n')

        # counting quorum regain messages-id '106003' in
        # /var/log/glusterfs/glusterd.log file before glusterd services start
        cmd_glusterd = f"grep -o '106003' {self.log_glusterd} | wc -l"
        ret = redant.execute_abstract_op_node(cmd_glusterd,
                                              self.server_list[0])
        before_glusterd_start_glusterd_id_count = ret['msg'][0].rstrip('\n')

        # Starting glusterd services
        redant.start_glusterd(self.server_list[1])

        # Checking glusterd service running or not
        ret = redant.is_glusterd_running(self.servers[1])
        if ret != 1:
            raise Exception("glusterd service should be running")

        # counting quorum messages-id '106003' in a file in a
        # /var/log/messages file after glusterd service start
        count = 0
        expected_msg_id_count = int(before_glusterd_start_msgid_count) + 2
        msg_count = False
        while count <= 10:
            ret = redant.execute_abstract_op_node(cmd_messages,
                                                  self.server_list[0])
            after_glusterd_start_msgid_count = ret['msg'][0].rstrip('\n')
            if (re.search(r'\b' + str(expected_msg_id_count) + r'\b',
                          after_glusterd_start_msgid_count)):
                msg_count = True
                break
            sleep(2)
            count += 1

        if not msg_count:
            raise Exception(f"Failed to grep quorum message-id "
                            f"106003 count in :{self.log_messages}")

        # counting quorum regain messages-id '106003' in
        # /var/log/glusterfs/glusterd.log file after glusterd services start
        ret = redant.execute_abstract_op_node(cmd_glusterd,
                                              self.server_list[0])
        after_glusterd_start_glusterd_id_count = ret['msg'][0].rstrip('\n')

        # Finding quorum regain message-id count difference between before
        # and after glusterd services start in /var/log/messages
        count_diff = (int(after_glusterd_start_msgid_count)
                      - int(before_glusterd_start_msgid_count))
        if count_diff != 2:
            raise Exception(f"Failed to record regain messages "
                            f"in : {self.log_messages}")

        # Finding quorum regain message-id count difference between before
        # and after glusterd services start in /var/log/glusterfs/glusterd.log
        count_diff = (int(after_glusterd_start_glusterd_id_count)
                      - int(before_glusterd_start_glusterd_id_count))
        if count_diff != 2:
            raise Exception(f"Failed to record regain messages "
                            f"in : {self.log_glusterd}")
