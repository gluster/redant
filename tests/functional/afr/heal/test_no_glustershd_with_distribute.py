"""
  Copyright (C) 2017-2021 Red Hat, Inc. <http://www.redhat.com>

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

# disruptive;
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    verifies the self-heal daemon process on multiple volumes running.
    """
    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        default_volume_type_config = {
            'rep': {
                'dist_count': 1,
                'replica_count': 2,
                'transport': 'tcp'},
            'disp': {
                'disperse_count': 6,
                'redundancy_count': 2,
                'transport': 'tcp'},
            'dist': {
                'dist_count': 3,
                'transport': 'tcp'},
            'dist-rep': {
                'dist_count': 2,
                'replica_count': 3,
                'transport': 'tcp'}
        }
        for vol_type, conf in default_volume_type_config.items():
            vol_name = f"{self.test_name}-{vol_type}"
            self.redant.setup_volume(vol_name, self.server_list[0],
                                     conf, self.server_list,
                                     self.brick_roots, force=True)

            # Verify volume's all process are online for 60 sec
            if not (self.redant.wait_for_volume_process_to_be_online(vol_name,
                    self.server_list[0], self.server_list, 60)):
                raise Exception("Failed to wait for volume processes to "
                                "be online")

        # Verfiy glustershd process releases its parent process
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

    def run_test(self, redant):
        """
        Test Script to verify the glustershd server vol file
        has only entries for replicate volumes

        * Create multiple volumes and start all volumes
        * Check the glustershd processes - Only 1 glustershd should be listed
        * Stop all volumes
        * Check the glustershd processes - No glustershd should be running
        * Start the distribute volume only
        * Check the glustershd processes - No glustershd should be running

        """
        # check the self-heal daemon process
        ret, glustershd_pids = (redant.
                                get_self_heal_daemon_pid(self.server_list))
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process "
                            f"found : {glustershd_pids}")

        # stop all the volumes
        volume_list = redant.get_volume_list(self.server_list[0])
        for volume in volume_list:
            redant.volume_stop(volume, self.server_list[0])

        # check the self-heal daemon process after stopping all volumes
        ret, glustershd_pids = (redant.
                                get_self_heal_daemon_pid(self.server_list))
        if ret:
            raise Exception("Self heal daemon process is still running "
                            "after stopping all volumes")

        for node in glustershd_pids:
            if glustershd_pids[node] != -1:
                raise Exception("Self heal daemon process is still running "
                                f"on node {node} after stopping volumes")

        # start the distribute volume only
        for volume in volume_list:
            volume_type_info = (redant.get_volume_type_info(
                                self.server_list[0], volume))
            volume_type = (volume_type_info['volume_type_info']['typeStr'])
            if volume_type == 'Distribute':
                redant.volume_start(volume, self.server_list[0])
                break

        # check the self-heal daemon process after starting distribute volume
        ret, glustershd_pids = (redant.
                                get_self_heal_daemon_pid(self.server_list))
        if ret:
            raise Exception("Self heal daemon process is still running "
                            "after starting only Distribute volume ")

        for node in glustershd_pids:
            if glustershd_pids[node] != -1:
                raise Exception("Self heal daemon process is still running "
                                f"on node {node} after stopping volumes")
