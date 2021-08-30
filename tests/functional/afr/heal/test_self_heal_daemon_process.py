"""
  Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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
        Test Cases in this module tests the self heal daemon process.
"""

# disruptive;rep,dist-rep,disp,dist-disp
# TODO: NFS, CIFS
import calendar
import time
import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    SelfHealDaemonProcessTests contains tests which verifies the
    self-heal daemon process of the nodes for different scenerios
    """
    def terminate(self):
        """
        Wait for IO to complete, if the TC fails early
        """
        try:
            if not self.io_validation_complete:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mounts)):
                    raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _test_glustershd_with_add_remove_brick(self):
        """
        Test script to verify glustershd process with adding and
        removing bricks

        * check glustershd process - only 1 glustershd process should
          be running
        * bricks must be present in glustershd-server.vol file for
          the replicated involved volumes
        * Add bricks
        * check glustershd process - only 1 glustershd process should
          be running and its should be different from previous one
        * bricks which are added must present in glustershd-server.vol file
        * remove bricks
        * check glustershd process - only 1 glustershd process should
          be running and its different from previous one
        * bricks which are removed should not present
          in glustershd-server.vol file

        """
        # Verfiy glustershd process releases its parent process
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        self.GLUSTERSHD = "/var/lib/glusterd/glustershd/glustershd-server.vol"

        # check the self-heal daemon process
        ret, glustershd_pids = (self.redant.
                                get_self_heal_daemon_pid(self.server_list))

        if not ret:
            raise Exception("Either No self heal daemon process found "
                            "or more than One self heal daemon process"
                            f" found : {glustershd_pids}")

        # get the bricks for the volume
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to get the bricks list")

        # validate the bricks present in volume info with
        # glustershd server volume file
        ret = self.redant.do_bricks_exist_in_shd_volfile(self.vol_name,
                                                         bricks_list,
                                                         self.server_list[0])
        if not ret:
            raise Exception("Brick List from volume info is "
                            "different from glustershd server "
                            "volume file. Please check log "
                            "file for details")

        # expanding volume
        force = False
        if self.volume_type == "dist-disp":
            force = True
        if not self.redant.expand_volume(self.server_list[0], self.vol_name,
                                         self.server_list,
                                         self.brick_roots, force):
            raise Exception("Failed to add bricks to volume "
                            f"{self.vol_name}")

        # Log Volume Info and Status after expanding the volume
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Verify volume's all process are online for 60 sec
        if not (self.redant.wait_for_volume_process_to_be_online(
                self.vol_name, self.server_list[0],
                self.server_list, 60)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Start Rebalance
        self.redant.rebalance_start(self.vol_name, self.server_list[0],
                                    force=True)

        # Log Rebalance status
        ret = self.redant.get_rebalance_status(self.vol_name,
                                               self.server_list[0])
        if ret is None:
            raise Exception("Rebalance status command has returned None")

        # Wait for rebalance to complete
        ret = (self.redant.
               wait_for_rebalance_to_complete(self.vol_name,
                                              self.server_list[0]))
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Check Rebalance status after rebalance is complete
        ret = self.redant.get_rebalance_status(self.vol_name,
                                               self.server_list[0])
        if ret is None:
            raise Exception("Rebalance status command has returned None")

        # Check the self-heal daemon process after adding bricks
        ret, pid_after_add = (self.redant.
                              get_self_heal_daemon_pid(self.server_list))
        if not ret:
            raise Exception("Either No self heal daemon process found "
                            "or more than One self heal daemon process"
                            f" found : {pid_after_add}")

        # Compare before and after pids
        if glustershd_pids != pid_after_add:
            raise Exception("Self Daemon process is same before and"
                            " after adding bricks")

        # get the bricks for the volume after expanding
        brick_after_add = self.redant.get_all_bricks(self.vol_name,
                                                     self.server_list[0])
        if brick_after_add is None:
            raise Exception("Failed to get the bricks list")

        # validate the bricks present in volume info
        # with glustershd server volume file after adding bricks
        ret = (self.redant.do_bricks_exist_in_shd_volfile(self.vol_name,
               brick_after_add, self.server_list[0]))
        if not ret:
            raise Exception("Brick List from volume info is "
                            "different from glustershd server "
                            "volume file after expanding bricks. "
                            "Please check log file for details")

        # shrink the volume
        ret = self.redant.shrink_volume(self.server_list[0],
                                        self.vol_name)
        if not ret:
            raise Exception("Failed to remove-brick from volume")

        # Log Volume Info and Status after shrinking the volume
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # get the bricks after shrinking the volume
        brick_after_shrink = self.redant.get_all_bricks(self.vol_name,
                                                        self.server_list[0])
        if brick_after_shrink is None:
            raise Exception("Failed to get brick list")

        if len(brick_after_shrink) != len(bricks_list):
            raise Exception("Brick Count is mismatched after "
                            "shrinking the volume self.vol_name")

        # Verfiy glustershd process releases its parent process
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # check the self-heal daemon process after removing bricks
        ret, pid_after_shrink = (self.redant.get_self_heal_daemon_pid(
                                 self.server_list))
        if not ret:
            raise Exception("Either No self heal daemon process found "
                            "or more than One self heal daemon process"
                            f" found : {pid_after_shrink}")

        # Compare before and after pids
        if pid_after_shrink != pid_after_add:
            raise Exception("Self Daemon process is same before and"
                            " after adding bricks")

        # validate bricks present in volume info
        # with glustershd server volume file after removing bricks
        ret = (self.redant.do_bricks_exist_in_shd_volfile(self.vol_name,
               brick_after_shrink, self.server_list[0]))
        if not ret:
            raise Exception("Brick List from volume info is "
                            "different from glustershd server "
                            "volume file after expanding bricks. "
                            "Please check log file for details")

    def _test_glustershd_with_restarting_glusterd(self):
        """
        Test Script to verify the self heal daemon process with restarting
        glusterd and rebooting the server

        * stop all volumes
        * restart glusterd - should not run self heal daemon process
        * start replicated involved volumes
        * single self heal daemon process running
        * restart glusterd
        * self heal daemon pid will change
        * bring down brick and restart glusterd
        * self heal daemon pid will change and its different from previous
        * brought up the brick
        """

        # stop the volume
        self.redant.volume_stop(self.vol_name, self.server_list[0])

        # this isn't a valid check as no process will be online for a volume
        # after volume stop
        # check the self heal daemon process after stopping volume
        if (self.redant.
            are_all_self_heal_daemons_online(self.vol_name,
                                             self.server_list[0])):
            raise Exception("Self Heal Daemon process is still running "
                            "even after stopping volume")

        # restart glusterd service on all the servers
        self.redant.restart_glusterd(self.server_list)
        if not self.redant.wait_for_glusterd_to_start(self.server_list):
            raise Exception("Failed to start glusterd")

        # this isn't a valid check as no process will be online for a volume
        # after after glusterd restart if a volume is stopped
        # check the self heal daemon process after restarting glusterd process
        if (self.redant.
            are_all_self_heal_daemons_online(self.vol_name,
                                             self.server_list[0])):
            raise Exception("Self Heal Daemon process is running after "
                            f"glusterd restart with volume {self.vol_name} in"
                            "stop state")

        # start the volume
        self.redant.volume_start(self.vol_name, self.server_list[0])

        # Verfiy glustershd process releases its parent process
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # get the self heal daemon pids after starting volume
        ret, pid_after_start = (self.redant.
                                get_self_heal_daemon_pid(
                                    self.server_list))
        if not ret:
            raise Exception("Either No self heal daemon process found "
                            "or more than One self heal daemon process"
                            f" found : {pid_after_start}")

        # get the bricks for the volume
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to get the bricks list")

        # validate the bricks present in volume info
        # with glustershd server volume file
        ret = (self.redant.do_bricks_exist_in_shd_volfile(self.vol_name,
               bricks_list, self.server_list[0]))
        if not ret:
            raise Exception("Brick List from volume info is "
                            "different from glustershd server "
                            "volume file after expanding bricks. "
                            "Please check log file for details")

        # restart glusterd service on all the servers
        self.redant.restart_glusterd(self.server_list)

        # Verify volume's all process are online for 60 sec
        if not (self.redant.wait_for_volume_process_to_be_online(
                self.vol_name, self.server_list[0],
                self.server_list, 60)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verfiy glustershd process releases its parent process
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # check the self heal daemon process after starting volume and
        # restarting glusterd process
        ret, pid_after_restart = (self.redant.get_self_heal_daemon_pid(
                                  self.server_list))
        if not ret:
            raise Exception("Either No self heal daemon process found "
                            "or more than One self heal daemon process"
                            f" found : {pid_after_restart}")

        # Compare before and after pids
        if pid_after_start == pid_after_restart:
            raise Exception("Self Daemon process is same before and"
                            " after adding bricks")

        # select the bricks to bring offline
        bricks_to_bring_offline = (self.redant.
                                   select_volume_bricks_to_bring_offline(
                                       self.vol_name, self.server_list[0]))
        # Bring down the selected bricks
        self.redant.bring_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline)
        if not self.redant.are_bricks_offline(self.vol_name,
                                              bricks_to_bring_offline,
                                              self.server_list[0]):
            raise Exception("Failed to bring down the bricks. Please "
                            "check the log file for more details.")

        # restart glusterd after brought down the brick
        self.redant.restart_glusterd(self.server_list)
        if not self.redant.wait_for_glusterd_to_start(self.server_list):
            raise Exception("Failed to start glusterd")

        # Verify volume's all process are online for 60 sec
        if not (self.redant.wait_for_volume_process_to_be_online(
                self.vol_name, self.server_list[0],
                self.server_list, 60)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verfiy glustershd process releases its parent process
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # check the self heal daemon process after killing brick and
        # restarting glusterd process
        ret, pid_after_brick_kill = (self.redant.get_self_heal_daemon_pid(
                                     self.server_list))
        if not ret:
            raise Exception("Either No self heal daemon process found "
                            "or more than One self heal daemon process"
                            f" found : {pid_after_brick_kill}")

        # Compare before and after pids
        if pid_after_brick_kill == pid_after_restart:
            raise Exception("Self Heal Daemon process are same from before "
                            "killing the brick,restarting glusterd process")

        # brought the brick online
        self.redant.bring_bricks_online(self.vol_name,
                                        self.server_list,
                                        bricks_to_bring_offline, True)
        if not self.redant.are_bricks_online(self.vol_name,
                                             bricks_to_bring_offline,
                                             self.server_list[0]):
            raise Exception("Failed to bring bricks: "
                            f"{bricks_to_bring_offline} online")

    def _test_brick_process_not_started_on_read_only_node_disks(self):
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
        self.io_validation_complete = True
        # Select bricks to bring offline
        bricks_to_bring_offline = \
            (self.redant.
             select_volume_bricks_to_bring_offline(self.vol_name,
                                                   self.server_list[0]))
        # Bring down the selected bricks
        self.redant.bring_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline)
        if not self.redant.are_bricks_offline(self.vol_name,
                                              bricks_to_bring_offline,
                                              self.server_list[0]):
            raise Exception("Failed to bring down the bricks. Please "
                            "check the log file for more details.")

        # Creating files for all volumes
        self.mounts = (self.redant.es.
                       get_mnt_pts_dict_in_list(self.vol_name))

        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # Create files
            self.redant.logger.info("Modifying files on "
                                    f"{mount_obj['client']}:"
                                    f"{mount_obj['mountpath']}")
            proc = self.redant.create_files(num_files=100,
                                            fix_fil_size="1k",
                                            path=mount_obj['mountpath'],
                                            node=mount_obj['client'])
            self.all_mounts_procs.append(proc)
        self.io_validation_complete = False

        # umount brick
        self.brick_node, volume_brick = bricks_to_bring_offline[0].split(':')
        self.brick = '/'.join(volume_brick.split('/')[0:3])
        self.redant.execute_abstract_op_node(f'umount -l {self.brick}',
                                             self.brick_node)

        # get time before remount the directory and checking logs for error
        time_before_checking_logs = (self.redant.execute_abstract_op_node(
                                     'date -u +%s', self.brick_node))
        time_before_checking_logs = (time_before_checking_logs['msg'][0].
                                     rstrip("\n"))

        # remount the directory with read-only option
        self.redant.execute_abstract_op_node(f'mount -o ro {self.brick}',
                                             self.brick_node)

        # start volume with "force" option
        self.redant.volume_start(self.vol_name, self.server_list[0],
                                 force=True)

        # Such errors is not found in gluster upstream/downstream
        # check logs for an 'initializing translator failed' error
        error_msg = 'posix: initializing translator failed'
        volume_brick = volume_brick.split('/')
        cmd = ("cat /var/log/glusterfs/bricks/"
               f"{volume_brick[-4]}-"
               f"{volume_brick[-3]}-{volume_brick[-2]}-"
               f"{volume_brick[-1]}.log | grep '{error_msg}'")
        ret = self.redant.execute_abstract_op_node(cmd, self.brick_node)
        log_msg = ret['msg'][0].rstrip().split('\n')[-1]
        if error_msg not in log_msg:
            raise Exception("Unexpected:: No errros found in log file")

        # get time from log message
        log_time_msg = log_msg.split('E')[0][1:-2].split('.')[0]
        log_time_msg_converted = calendar.timegm(time.strptime(
            log_time_msg, '%Y-%m-%d %H:%M:%S'))

        # get time after remount the directory checking logs for error
        time_after_checking_logs = (self.redant.execute_abstract_op_node(
                                    'date -u +%s', self.brick_node))
        time_after_checking_logs = (time_after_checking_logs['msg'][0].
                                    rstrip("\n"))

        # check time periods
        if (int(time_before_checking_logs) > int(log_time_msg_converted)
           or int(log_time_msg_converted) > int(time_after_checking_logs)):
            raise Exception('Expected error is not in right time period')

        # umount brick
        self.redant.execute_abstract_op_node(f'umount -l {self.brick}',
                                             self.brick_node)

        # remount the directory with read-write option
        self.redant.execute_abstract_op_node(f'mount {self.brick}',
                                             self.brick_node)

        # start volume with "force" option
        self.redant.volume_start(self.vol_name, self.server_list[0],
                                 force=True)

        # Validate IO
        ret = self.redant.validate_io_procs(self.procs_list, self.mounts)
        if not ret:
            raise Exception("IO validation failed")
        self.io_validation_complete = True

    def run_test(self, redant):
        """
        1.Test shd with add-remove brick
        2.Test shd with restart glusterd
        3.Test brick process not started on read only node
        """
        self._test_glustershd_with_add_remove_brick()
        redant.logger.info("Test for add remove brick successful")
        self._test_glustershd_with_restarting_glusterd()
        redant.logger.info("Test for restart glusterd successful")
        self._test_brick_process_not_started_on_read_only_node_disks()
        redant.logger.info("Test for brick process successful")
