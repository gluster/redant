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
    SelfHealDaemonProcessTests contains tests which verifies the
    self-heal daemon process of the nodes
"""

# disruptive;rep
# TODO: nfs

import traceback
import calendar
import time
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """
        Remount the bricks and complete the IO if the TC failed early
        """
        try:
            if self.is_unmounted:
                if not self.redant.wait_for_io_to_complete(self.procs_list,
                                                           self.mounts):
                    raise Exception("Failed to wait fore IO to complete")

                self.redant.volume_stop(self.vol_name, self.server_list[0],
                                        force=True)

                self.redant.execute_abstract_op_node(f'umount {self.brick}',
                                                     self.brick_node, False)
                self.redant.execute_abstract_op_node(f'mount {self.brick}',
                                                     self.brick_node, False)

        except Exception as err:
            tb = traceback.format_exc()
            self.redant.logger.error(err)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        * create volume and start
        * kill one brick
        * start IO
        * unmount the brick directory from node
        * remount the brick directory with read-only option
        * start the volume with "force" option
        * check for error 'posix: initializing translator failed' in log file
        * remount the brick directory with read-write option
        * start the volume with "force" option
        * validate IO
        """
        self.is_unmounted = False
        self.procs_list = []
        self.glustershd = "/var/lib/glusterd/glustershd/glustershd-server.vol"
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Select bricks to bring offline
        bricks_to_bring_offline = (redant.
                                   select_volume_bricks_to_bring_offline(
                                       self.vol_name,
                                       self.server_list[0]))

        # Bring brick offline
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)
        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} "
                            "not yet offline")

        # Creating files for all volumes
        for mount_obj in self.mounts:
            proc = (redant.
                    create_files(num_files=100,
                                 fix_fil_size="1k",
                                 path=f"{mount_obj['mountpath']}/test_dir",
                                 node=mount_obj['client'],
                                 base_file_name="test_file"))

            self.procs_list.append(proc)

        # umount brick
        self.brick_node, volume_brick = bricks_to_bring_offline[0].split(':')
        self.brick = '/'.join(volume_brick.split('/')[0:3])
        redant.execute_abstract_op_node(f'umount -l {self.brick}',
                                        self.brick_node)
        self.is_unmounted = True

        # get time before remount the directory and checking logs for error
        time_before_checking_logs = (redant.execute_abstract_op_node(
                                     'date -u +%s', self.brick_node))
        time_before_checking_logs = (time_before_checking_logs['msg'][0].
                                     rstrip("\n"))

        # remount the directory with read-only option
        redant.execute_abstract_op_node(f'mount -o ro {self.brick}',
                                        self.brick_node)

        # start volume with "force" option
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # check logs for an 'initializing translator failed' error

        error_msg = 'posix: initializing translator failed'
        volume_brick = volume_brick.split('/')
        cmd = ("cat /var/log/glusterfs/bricks/"
               f"{volume_brick[-3]}-{volume_brick[-2]}-"
               f"{volume_brick[-1]}.log | grep '{error_msg}'")
        ret = redant.execute_abstract_op_node(cmd, self.brick_node)
        log_msg = ret['msg'][0].rstrip().split('\n')[-1]

        if error_msg not in log_msg:
            raise Exception("Unexpected:: No errros found in log file")

        # get time from log message
        log_time_msg = log_msg.split('E')[0][1:-2].split('.')[0]
        log_time_msg_converted = calendar.timegm(time.strptime(
            log_time_msg, '%Y-%m-%d %H:%M:%S'))

        # get time after remount the directory checking logs for error
        time_after_checking_logs = (redant.execute_abstract_op_node(
                                    'date -u +%s', self.brick_node))
        time_after_checking_logs = (time_after_checking_logs['msg'][0].
                                    rstrip("\n"))

        # check time periods
        if (int(time_before_checking_logs) > int(log_time_msg_converted)
           or int(log_time_msg_converted) > int(time_after_checking_logs)):
            raise Exception('Expected error is not in right time period')

        # umount brick
        redant.execute_abstract_op_node(f'umount -l {self.brick}',
                                        self.brick_node)

        # remount the directory with read-write option
        redant.execute_abstract_op_node(f'mount {self.brick}',
                                        self.brick_node)
        self.is_unmounted = True

        # start volume with "force" option
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        ret = redant.validate_io_procs(self.procs_list, self.mounts)
        if not ret:
            raise Exception("IO validation failed")
