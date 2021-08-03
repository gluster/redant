"""
 Copyright (C) 2016-2018  Red Hat, Inc. <http://www.redhat.com>

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
    TC to verify the self-heal daemon process on multiple volumes running.
"""

# disruptive;
from tests.d_parent_test import DParentTest


class TestSelfHealDaemonProcessTestsWithMultipleVolumes(DParentTest):

    def run_test(self, redant):
        """
        * Create multiple volumes and start all volumes
        * Check the glustershd processes - Only One glustershd should be listed
        * Check the glustershd server vol file - should contain entries only
                                             for replicated involved volumes
        * Add bricks to the replicate volume - it should convert to
                                               distributed-replicate
        * Check the glustershd server vol file - newly added bricks
                                                 should present
        * Check the glustershd processes - Only 1 glustershd should be listed

        """
        # Create and start multiple volumes
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
                'dist_count': 2,
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
            if not (redant.wait_for_volume_process_to_be_online(vol_name,
                    self.server_list[0], self.server_list, 60)):
                raise Exception("Failed to wait for volume processes to "
                                "be online")

        # Verfiy glustershd process releases its parent process
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        self.GLUSTERSHD = "/var/lib/glusterd/glustershd/glustershd-server.vol"

        # check the self-heal daemon process
        ret, glustershd_pids = (redant.
                                get_self_heal_daemon_pid(self.server_list))

        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process "
                            f"found : {glustershd_pids}")

        # For all the volumes, check whether bricks present in
        # glustershd server vol file
        volume_list = redant.get_volume_list(self.server_list[0])
        for volume in volume_list:
            vol_type_info = redant.get_volume_type_info(self.server_list[0],
                                                        volume)
            volume_type = vol_type_info['volume_type_info']['typeStr']

            # get the bricks for the volume
            bricks_list = redant.get_all_bricks(volume, self.server_list[0])
            if bricks_list is None:
                raise Exception("Failed to get the bricks list")

            # validate the bricks present in volume info with
            # glustershd server volume file
            ret = redant.do_bricks_exist_in_shd_volfile(volume, bricks_list,
                                                        self.server_list[0])
            if volume_type == 'Distribute':
                if ret:
                    raise Exception("Bricks exist in glustershd server "
                                    f"volume file for {volume_type} Volume")
            else:
                if not ret:
                    raise Exception("Brick List from volume info is "
                                    "different from glustershd server "
                                    "volume file. Please check log "
                                    "file for details")

        # expanding volume for Replicate
        for volume in volume_list:
            vol_type_info = redant.get_volume_type_info(self.server_list[0],
                                                        volume)
            volume_type = vol_type_info['volume_type_info']['typeStr']
            if volume_type == 'Replicate':
                if not redant.expand_volume(self.server_list[0], volume,
                                            self.server_list,
                                            self.brick_roots):
                    raise Exception("Failed to add bricks to volume "
                                    f"{volume}")

                # Log Volume Info and Status after expanding the volume
                if not (redant.log_volume_info_and_status(self.server_list[0],
                        volume)):
                    raise Exception("Logging volume info and status failed "
                                    f"on volume {volume}")

                # Verify volume's all process are online for 60 sec
                if not (redant.wait_for_volume_process_to_be_online(volume,
                        self.server_list[0], self.server_list, 60)):
                    raise Exception("Failed to wait for volume processes to "
                                    "be online")

                # check the type for the replicate volume
                vol_type_for_replicate_after_adding_bricks = \
                    redant.get_volume_type_info(self.server_list[0], volume)
                vol_type_for_replicate_after_adding_bricks = \
                    (vol_type_for_replicate_after_adding_bricks
                     ['volume_type_info']['typeStr'])

                if vol_type_for_replicate_after_adding_bricks != \
                   "Distributed-Replicate":
                    raise Exception("Replicate volume type is not converted "
                                    "to Distributed-Replicate after adding "
                                    "bricks")

                # get the bricks for the volume after expanding
                new_brick_list = redant.get_all_bricks(self.server_list[0],
                                                       volume)
                if new_brick_list is None:
                    raise Exception("Failed to get brick list")

                # validate the bricks present in volume info
                # with glustershd server volume file after adding bricks
                ret = (redant.do_bricks_exist_in_shd_volfile(volume,
                       new_brick_list, self.server_list[0]))
                if not ret:
                    raise Exception("Brick List from volume info is "
                                    "different from glustershd server "
                                    "volume file after expanding bricks. "
                                    "Please check log file for details")

        # check the self-heal daemon process
        ret, glustershd_pids_after_adding_bricks = \
            redant.get_self_heal_daemon_pid(self.server_list)
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process "
                            f"found : {glustershd_pids_after_adding_bricks}")

        if glustershd_pids == glustershd_pids_after_adding_bricks:
            raise Exception("Self Daemon process is same before and"
                            " after adding bricks")
