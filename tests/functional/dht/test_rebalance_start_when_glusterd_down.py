"""
 Copyright (C) 2019-2020 Red Hat, Inc. <http://www.redhat.com>

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
    TC to test rebalance start when glusterd down
"""

# disruptive;dist
from random import choice
from tests.d_parent_test import DParentTest


class TestRebalanceValidation(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        - Create and start a volume
        - Mount the volume on clients
        - Perform some IO on mountpoint
        - Expand the volume
        - Stop glusterd on a random node
        - Start rebalance on the volume
        - Wait for rebalance to complete, the status should be failed
        - Confirm that rebalance failed with proper error msg
        """
        # Perform IO on mountpoint
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.proc_list = []
        index = 0
        for index, mount_obj in enumerate(self.mounts, start=1):
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      index + 10, 1, 1, 1, 1,
                                                      mount_obj['client'])
            self.proc_list.append(proc)

        if not redant.validate_io_procs(self.proc_list, self.mounts):
            raise Exception("Failed to perform IO on some clients")

        if not redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to list file/dirs from mountpoint")

        # Expanding volume by adding bricks to the volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception("Failed to expand volume")

        # Get all servers IP addresses which are part of volume
        ret = redant.get_all_bricks(self.vol_name, self.server_list[0])
        list_of_servers_used = []
        for brick in ret:
            host = brick.split(":")[0]
            if host not in list_of_servers_used:
                list_of_servers_used.append(host)

        # Form a new list of servers without mnode in it to prevent mnode
        # from glusterd failure
        if self.server_list[0] in list_of_servers_used:
            list_of_servers_used.remove(self.server_list[0])

        # Stop glusterd on a server
        self.random_server = choice(list_of_servers_used)
        redant.stop_glusterd(self.random_server)

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0])
        if ret:
            raise Exception("Unexpected: Rebalance is successful")

        error_msg1 = "\"fix layout on / failed\""
        error_msg2 = "\"Transport endpoint is not connected\""
        cmd = (f"grep -w {error_msg1} /var/log/glusterfs/{self.vol_name}-"
               f"rebalance.log | grep -w {error_msg2}")
        redant.execute_abstract_op_node(cmd, self.server_list[0])
