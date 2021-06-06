"""
 Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>

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
    No Errors should generate in brick logs after deleting files
    from mountpoint
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;dist-rep


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway then wait for IO to comlete before
        calling the terminate function of DParentTest
        """
        try:
            ret = self.redant.wait_for_io_to_complete(self.list_of_procs,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        '''
        -> Create volume
        -> Mount volume
        -> write files on mount point
        -> delete files from mount point
        -> check for any errors filled in all brick logs
        '''

        # Get mountpoint list
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Check if the volume is mounted
        for mount_obj in self.mnt_list:
            ret = redant.is_mounted(self.vol_name, mount_obj['mountpath'],
                                    mount_obj['client'], self.server_list[0])
            if not ret:
                raise Exception(f"Volume {self.vol_name} is not mounted")

        # run IO on mountpoint
        self.list_of_procs = []
        self.counter = 1
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      self.counter,
                                                      2, 5, 3, 10,
                                                      mount_obj['client'])

            self.list_of_procs.append(proc)
            self.counter += 10

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # Getting timestamp
        ret = redant.execute_abstract_op_node('date +%s', self.server_list[0])
        timestamp = ret['msg'][0].rstrip('\n')

        # Getting all bricks
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get brick list")

        # Creating dictionary for each node brick path,
        # here nodes are keys and brick paths are values
        brick_path_dict = {}
        for brick in brick_list:
            node, brick_path = brick.split(r':')
            brick_path_list = brick_path.split(r'/')
            del brick_path_list[0]
            brick_log_path = '-'.join(brick_path_list)
            brick_path_dict[node] = brick_log_path

        brick_log_dir = "/var/log/glusterfs/bricks"
        for node in brick_path_dict:
            #  Copying brick logs into other file for backup purpose
            cmd = (f"cp {brick_log_dir}/{brick_path_dict[node]}.log "
                   f"{brick_log_dir}/{brick_path_dict[node]}_{timestamp}.log")
            redant.execute_abstract_op_node(cmd, node)

            # Clearing the existing brick log file
            cmd = f"> {brick_log_dir}/{brick_path_dict[node]}.log"
            ret = redant.execute_abstract_op_node(cmd, node)

        # Deleting files from mount point
        cmd = f"rm -rf {self.mnt_list[0]['mountpath']}/*"
        ret = redant.execute_abstract_op_node(cmd, self.mnt_list[0]['client'])

        # Searching for error messages in brick logs after deleting
        # files from mountpoint
        for node in brick_path_dict:
            cmd = (f"grep ' E ' {brick_log_dir}/{brick_path_dict[node]}.log"
                   " | wc -l")
            ret = redant.execute_abstract_op_node(cmd, node)
            if int(ret['msg'][0].rstrip('\n')) != 0:
                raise Exception("Found error messages in brick logs on"
                                f" {node}")
