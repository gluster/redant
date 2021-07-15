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
@runs_on([['replicated', 'distributed-replicated', 'dispersed',
           'distributed-dispersed'], ['glusterfs', 'nfs']])
"""
# nonDisruptive;rep
# TODO: nfs

import calendar
import time
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

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
        self.all_mounts_procs = []
        self.glustershd = "/var/lib/glusterd/glustershd/glustershd-server.vol"
        # Select bricks to bring offline
        # bricks_to_bring_offline_dict = (select_bricks_to_bring_offline(
        #     self.mnode, self.volname))
        # bricks_to_bring_offline = bricks_to_bring_offline_dict['volume_bricks']

        # # Bring brick offline
        # g.log.info('Bringing bricks %s offline...', bricks_to_bring_offline)
        # ret = bring_bricks_offline(self.volname, bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks %s offline' %
        #                 bricks_to_bring_offline)

        # ret = are_bricks_offline(self.mnode, self.volname,
        #                          bricks_to_bring_offline)
        # self.assertTrue(ret, 'Bricks %s are not offline'
        #                 % bricks_to_bring_offline)
        # g.log.info('Bringing bricks %s offline is successful',
        #            bricks_to_bring_offline)

        # # Creating files for all volumes
        # for mount_obj in self.mounts:
        #     g.log.info("Starting IO on %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     cmd = ("/usr/bin/env python %s create_files -f 100 "
        #            "%s/%s/test_dir" % (
        #                self.script_upload_path,
        #                mount_obj.mountpoint, mount_obj.client_system))
        #     proc = g.run_async(mount_obj.client_system, cmd,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)

        # # umount brick
        # brick_node, volume_brick = bricks_to_bring_offline[0].split(':')
        # node_brick = '/'.join(volume_brick.split('/')[0:3])
        # g.log.info('Start umount brick %s...', node_brick)
        # ret, _, _ = g.run(brick_node, 'umount -l %s' % node_brick)
        # self.assertFalse(ret, 'Failed to umount brick %s' % node_brick)
        # g.log.info('Successfully umounted %s', node_brick)

        # # get time before remount the directory and checking logs for error
        # g.log.info('Getting time before remount the directory and '
        #            'checking logs for error...')
        # _, time_before_checking_logs, _ = g.run(brick_node, 'date -u +%s')
        # g.log.info('Time before remount the directory and checking logs - %s',
        #            time_before_checking_logs)

        # # remount the directory with read-only option
        # g.log.info('Start remount brick %s with read-only option...',
        #            node_brick)
        # ret, _, _ = g.run(brick_node, 'mount -o ro %s' % node_brick)
        # self.assertFalse(ret, 'Failed to remount brick %s' % node_brick)
        # g.log.info('Successfully remounted %s with read-only option',
        #            node_brick)

        # # start volume with "force" option
        # g.log.info('starting volume with "force" option...')
        # ret, _, _ = volume_start(self.mnode, self.volname, force=True)
        # self.assertFalse(ret, 'Failed to start volume %s with "force" option'
        #                  % self.volname)
        # g.log.info('Successfully started volume %s with "force" option',
        #            self.volname)

        # # check logs for an 'initializing translator failed' error
        # g.log.info("Checking logs for an 'initializing translator failed' "
        #            "error for %s brick...", node_brick)
        # error_msg = 'posix: initializing translator failed'
        # cmd = ("cat /var/log/glusterfs/bricks/%s-%s-%s.log | "
        #        "grep '%s'"
        #        % (volume_brick.split('/')[-3], volume_brick.split('/')[-2],
        #           volume_brick.split('/')[-1], error_msg))
        # ret, log_msgs, _ = g.run(brick_node, cmd)
        # log_msg = log_msgs.rstrip().split('\n')[-1]

        # self.assertTrue(error_msg in log_msg, 'No errors in logs')
        # g.log.info('EXPECTED: %s', error_msg)

        # # get time from log message
        # log_time_msg = log_msg.split('E')[0][1:-2].split('.')[0]
        # log_time_msg_converted = calendar.timegm(time.strptime(
        #     log_time_msg, '%Y-%m-%d %H:%M:%S'))
        # g.log.info('Time_msg from logs - %s ', log_time_msg)
        # g.log.info('Time from logs - %s ', log_time_msg_converted)

        # # get time after remount the directory checking logs for error
        # g.log.info('Getting time after remount the directory and '
        #            'checking logs for error...')
        # _, time_after_checking_logs, _ = g.run(brick_node, 'date -u +%s')
        # g.log.info('Time after remount the directory and checking logs - %s',
        #            time_after_checking_logs)

        # # check time periods
        # g.log.info('Checking if an error is in right time period...')
        # self.assertTrue(int(time_before_checking_logs) <=
        #                 int(log_time_msg_converted) <=
        #                 int(time_after_checking_logs),
        #                 'Expected error is not in right time period')
        # g.log.info('Expected error is in right time period')

        # # umount brick
        # g.log.info('Start umount brick %s...', node_brick)
        # ret, _, _ = g.run(brick_node, 'umount -l %s' % node_brick)
        # self.assertFalse(ret, 'Failed to umount brick %s' % node_brick)
        # g.log.info('Successfully umounted %s', node_brick)

        # # remount the directory with read-write option
        # g.log.info('Start remount brick %s with read-write option...',
        #            node_brick)
        # ret, _, _ = g.run(brick_node, 'mount %s' % node_brick)
        # self.assertFalse(ret, 'Failed to remount brick %s' % node_brick)
        # g.log.info('Successfully remounted %s with read-write option',
        #            node_brick)

        # # start volume with "force" option
        # g.log.info('starting volume with "force" option...')
        # ret, _, _ = volume_start(self.mnode, self.volname, force=True)
        # self.assertFalse(ret, 'Failed to start volume %s with "force" option'
        #                  % self.volname)
        # g.log.info('Successfully started volume %s with "force" option',
        #            self.volname)

        # # Validate IO
        # g.log.info('Validating IO on all mounts')
        # self.assertTrue(
        #     validate_io_procs(self.all_mounts_procs, self.mounts),
        #     "IO failed on some of the clients"
        # )
        # g.log.info('Successfully Validated IO on all mounts')
        # self.io_validation_complete = True
