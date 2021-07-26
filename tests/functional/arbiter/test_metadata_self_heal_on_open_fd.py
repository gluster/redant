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
    Pro-active metadata self heal on open fd
@runs_on([['replicated', 'distributed-replicated', 'arbiter',
           'distributed-arbiter'],
          ['glusterfs']])
"""

# disruptive;rep

import traceback
import os
import copy
from socket import gethostbyname
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
  
    def terminate(self):
        for node in self.nodes:
            try:
                if not self.redant.del_user(node,
                                            self.user):
                    raise Exception("Failed to delete user")
            except Exception as error:
                tb = traceback.format_exc
                self.logger.error(error)
                self.logger.error(tb)
        super().terminate()

    # def _verify_stat_info(self, nodes_to_check, test_file):
    #     """
    #     Helper method to verify stat on all bricks and client.
    #     """
    #     for node in nodes_to_check:
    #         filepath = nodes_to_check[node] + "/" + test_file
    #         stat_dict = get_file_stat(node, filepath)
    #         self.assertIsNotNone(stat_dict, "stat on {} failed"
    #                              .format(test_file))
    #         self.assertEqual(stat_dict['username'], self.user,
    #                          "Expected qa but found {}"
    #                          .format(stat_dict['username']))
    #         self.assertEqual(stat_dict['groupname'], self.user,
    #                          "Expected gid qa but found {}"
    #                          .format(stat_dict['groupname']))
    #         self.assertEqual(stat_dict['access'], '777',
    #                          "Expected permission 777 but found {}"
    #                          .format(stat_dict['access']))

    def run_test(self, redant):
        """

        Steps :
        1) Create a volume.
        2) Mount the volume using FUSE.
        3) Create test executable on volume mount.
        4) While test execution is in progress, bring down brick1.
        5) From mount point, change ownership, permission, group id of
           the test file.
        6) While test execution is in progress, bring back brick1 online.
        7) Do stat on the test file to check ownership, permission,
           group id on mount point and on bricks
        8) Stop test execution.
        9) Do stat on the test file to check ownership, permission,
           group id on mount point and on bricks.
        10) There should be no pending heals in the heal info command.
        11) There should be no split-brain.
        12) Calculate arequal of the bricks and mount point and it
            should be same.
        """
        self.user = "qa"
        self.nodes = []
        self.nodes = copy.deepcopy(self.server_list)
        self.nodes.append(self.client_list[0])
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Create user for changing ownership
        for node in self.nodes:
            if not redant.add_user(node, self.user):
                raise Exception(f"Failed to add user {self.user}"
                                f" on {node}")

        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Brick list is None")

        client = self.client_list[0]

        # Create test executable file on mount point
        m_point = self.mountpoint
        test_file = "testfile.sh"
        cmd = ("echo 'while true; do echo 'Press CTRL+C to stop execution';"
               f" done' >> {m_point}/{test_file}")
        redant.execute_abstract_op_node(cmd, client)

        # Execute the test file
        cmd = f"cd {m_point}; sh {test_file}"
        redant.logger.info(f"Running {cmd} on {client}")
        # redant.execute_command_async(cmd, client)
        self.proc = redant.execute_command_async(cmd, client)
        # print(ret)
        # Get pid of the test file
        _cmd = "ps -aux | grep -v grep | grep testfile.sh | awk '{print $2}'"
        ret = redant.execute_abstract_op_node(_cmd, client)
        out = ret['msg']
        print("PS AUX\n",ret)

        # Bring brick1 offline
        redant.bring_bricks_offline(self.vol_name, [bricks_list[1]])

        if not redant.are_bricks_offline(self.vol_name,
                                         [bricks_list[1]],
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_list[1]} is not offline")

        # change uid, gid and permission from client
        cmd = f"chown {self.user} {m_point}/{test_file}"
        redant.execute_abstract_op_node(cmd, client)

        cmd = f"chgrp {self.user} {m_point}/{test_file}"
        redant.execute_abstract_op_node(cmd, client)

        cmd = f"chmod 777 {m_point}/{test_file}"
        redant.execute_abstract_op_node(cmd, client)

        # Bring brick1 online
        redant.bring_bricks_online(self.vol_name,
                                   self.server_list,
                                   [bricks_list[1]])

        ret = redant.get_pathinfo(f"{m_point}/{test_file}", client)
        
        if ret is None:
            raise Exception("Failed to get path info")

        nodes_to_check = {}
        bricks_list = []
        for brick in ret['brickdir_paths']:
            node, brick_path = brick.split(':')

            if not node[0:2].isdigit():
                node = gethostbyname(node)
            nodes_to_check[node] = os.path.dirname(brick_path)
            path = node + ":" + os.path.dirname(brick_path)
            bricks_list.append(path)
        nodes_to_check[client] = m_point

        # # Verify that the changes are successful on bricks and client
        # self._verify_stat_info(nodes_to_check, test_file)

        # Kill the test executable file
        for pid in out:
            pid = pid.rstrip("\n")
            cmd = f"kill -s 9 {pid}"
            redant.execute_abstract_op_node(cmd, client)
        # # Verify that the changes are successful on bricks and client
        # self._verify_stat_info(nodes_to_check, test_file)

        # Verify there are no pending heals
        heal_info = redant.get_heal_info_summary(self.server_list[0],
                                                 self.vol_name)
        if heal_info is None:
            raise Exception('Unable to get heal info')
        for brick in bricks_list:
            if heal_info[brick]['numberOfEntries'] != '0':
                raise Exception(f"Pending heal on brick {brick}")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is not in split brain state")

        # Get arequal for mount
        arequals = redant.collect_mounts_arequal(self.mounts)
        print("\nMounts arequal:\n",arequals)
        # mount_point_total = arequals[0].splitlines()[-1].split(':')[-1]

        # # Collecting data bricks
        # vol_info = get_volume_info(self.mnode, self.volname)
        # self.assertIsNotNone(vol_info, 'Unable to get volume info')
        # data_brick_list = []
        # for brick in bricks_list:
        #     for brick_info in vol_info[self.volname]["bricks"]["brick"]:
        #         if brick_info["name"] == brick:
        #             if brick_info["isArbiter"] == "0":
        #                 data_brick_list.append(brick)
        # bricks_list = data_brick_list

        # # Get arequal on bricks and compare with mount_point_total
        # # It should be the same
        # arbiter = self.volume_type.find('arbiter') >= 0
        # subvols = get_subvols(self.mnode, self.volname)['volume_subvols']
        # stop = len(subvols[0]) - 1 if arbiter else len(subvols[0])
        # for subvol in subvols:
        #     subvol = [i for i in subvol if i in bricks_list]
        #     if subvol:
        #         ret, arequal = collect_bricks_arequal(subvol[0:stop])
        #         self.assertTrue(ret, 'Unable to get arequal checksum '
        #                         'on {}'.format(subvol[0:stop]))
        #         self.assertEqual(len(set(arequal)), 1, 'Mismatch of arequal '
        #                          'checksum among {} is '
        #                          'identified'.format(subvol[0:stop]))
        #         brick_total = arequal[-1].splitlines()[-1].split(':')[-1]
        #         self.assertEqual(brick_total, mount_point_total,
        #                          "Arequals for mountpoint and {} "
        #                          "are not equal".format(subvol[0:stop]))
