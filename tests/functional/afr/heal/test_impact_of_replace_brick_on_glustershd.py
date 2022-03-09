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
    Test Script to check impact of replace brick on shd and verify
    the glustershd server vol file has only entries for replicate volumes.
"""

# disruptive;

from random import choice
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    This test verifies the self-heal daemon process on
    multiple volumes running.
    """
    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Check for RHGS installation
        self.redant.check_gluster_installation(self.server_list, "downstream")

        default_volume_type_config = {
            'rep': {
                'dist_count': 1,
                'replica_count': 2,
                'transport': 'tcp'},
            'disp': {
                'disperse_count': 6,
                'redundancy_count': 2,
                'transport': 'tcp'},
            'dist-rep': {
                'dist_count': 2,
                'replica_count': 3,
                'transport': 'tcp'}
        }
        # Create and start multiple volumes
        for vol_type, conf in default_volume_type_config.items():
            vol_name = f"testvol-{vol_type}"
            self.redant.setup_volume(vol_name, self.server_list[0],
                                     conf, self.server_list,
                                     self.brick_roots, force=True)

            # Verify volume's all process are online for 60 sec
            if not (self.redant.wait_for_volume_process_to_be_online(
                    vol_name, self.server_list[0], self.server_list,
                    60)):
                raise Exception("Failed to wait for volume processes "
                                "to be online")

        # Verfiy glustershd process releases its parent process
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")
        self.GLUSTERSHD = "/var/lib/glusterd/glustershd/glustershd-server.vol"

    def run_test(self, redant):
        """
        Test Script to verify the glustershd server vol file
        has only entries for replicate volumes
        1.Create multiple volumes and start all volumes
        2.Check the glustershd processes - Only 1 glustershd should be listed
        3.Do replace brick on the replicate volume
        4.Confirm that the brick is replaced
        5.Check the glustershd processes - Only 1 glustershd should be listed
                                           and pid should not be same
        6.glustershd server vol should be updated with new bricks
        """

        # check the self-heal daemon process
        ret, glustershd_pids = (redant.
                                get_self_heal_daemon_pid(self.server_list))
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process "
                            f"found : {glustershd_pids}")

        volume_list = redant.get_volume_list(self.server_list[0])

        for volume in volume_list:
            # Log Volume Info and Status before replacing brick
            if not (redant.log_volume_info_and_status(self.server_list[0],
                                                      volume)):
                raise Exception("Logging volume info and status failed "
                                f"on volume {volume}")

            # Selecting a random source brick to replace
            src_brick = choice(redant.get_all_bricks(
                               volume, self.server_list[0]))
            node = src_brick.split(':')[0]
            _, dest_brick = redant.form_brick_cmd(node,
                                                  self.brick_roots,
                                                  volume, 1,
                                                  True)

            # Replace brick for the volume
            if not redant.replace_brick(self.server_list[0], volume,
                                        src_brick, dest_brick):
                raise Exception(f"Failed to replace brick: {src_brick}")

            # Verify all volume process are online
            if not (redant.wait_for_volume_process_to_be_online(
                    volume, self.server_list[0],
                    self.server_list)):
                raise Exception("Volume processes not yet online")

            # Check the self-heal daemon process after replacing brick
            ret, pid_after_replace = (redant.get_self_heal_daemon_pid(
                                      self.server_list))
            if not ret:
                raise Exception("Either No self heal daemon process "
                                "found or more than One self heal "
                                "daemon process "
                                f"found : {pid_after_replace}")

            # Compare the glustershd pids
            if glustershd_pids == pid_after_replace:
                raise Exception("Self heal Daemon process is same before "
                                "and after replacing bricks")

            # Get the bricks for the volume
            brick_list = redant.get_all_bricks(volume,
                                               self.server_list[0])
            if brick_list is None:
                raise Exception("Empty bricks list after replacing")

            # Validate the bricks present in volume info with
            # glustershd server volume file
            if not (redant.
                    do_bricks_exist_in_shd_volfile(volume,
                                                   brick_list,
                                                   self.server_list[0])):
                raise Exception("Brick List from volume info is different "
                                "from glustershd server volume file after "
                                "replacing bricks. Please check log file "
                                "for details")
