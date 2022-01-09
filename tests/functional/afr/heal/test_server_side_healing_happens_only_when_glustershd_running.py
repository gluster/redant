"""
 Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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

# disruptive;rep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    verifies the self-heal daemon process on a single volume
    """

    def run_test(self, redant):
        """
        Test Script which verifies that the server side healing must happen
        only if the heal daemon is running on the node where source brick
        resides.

         * Create and start the Replicate volume
         * Check the glustershd processes - Only 1 glustershd should be listed
         * Bring down the bricks without affecting the cluster
         * Create files on volume
         * kill the glustershd on node where bricks is running
         * bring the bricks up which was killed in previous steps
         * check the heal info - heal info must show pending heal info, heal
           shouldn't happen since glustershd is down on source node
         * issue heal
         * trigger client side heal
         * heal should complete successfully
        """

        # Verfiy glustershd process releases its parent process
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # Disable granular heal if not disabled already
        granular = redant.get_volume_options(self.vol_name,
                                             'granular-entry-heal',
                                             self.server_list[0])
        if granular['cluster.granular-entry-heal'] == 'on':
            if not redant.disable_granular_heal(self.vol_name,
                                                self.server_list[0]):
                raise Exception("Failed to disable granular-entry-heal")

        # Setting Volume options
        options = {"metadata-self-heal": "on",
                   "entry-self-heal": "on",
                   "data-self-heal": "on"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0], True)

        # Check the self-heal daemon process
        ret, pids = redant.get_self_heal_daemon_pid(self.server_list)
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process "
                            f"found : {pids}")

        # Select the bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Bring down the selected bricks
        if not redant.bring_bricks_offline(self.vol_name,
                                           offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        # Write files on all mounts
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        all_mounts_procs = []
        for mount_obj in self.mnt_list:
            proc = redant.create_files(num_files=100,
                                       fix_fil_size="1k",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'],
                                       base_file_name="file")
            all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(all_mounts_procs, self.mnt_list):
            raise Exception("IO validation failed")

        # Get online bricks list
        online_bricks = redant.get_online_bricks_list(self.vol_name,
                                                      self.server_list[0])

        # Get the nodes where bricks are running
        bring_offline_glustershd_nodes = []
        for brick in online_bricks:
            bring_offline_glustershd_nodes.append(brick.split(":")[0])

        # Kill the self heal daemon process on nodes
        if not (redant.bring_self_heal_daemon_process_offline(
                bring_offline_glustershd_nodes)):
            raise Exception("Unable to bring self heal daemon process "
                            "offline for nodes: "
                            f"{bring_offline_glustershd_nodes}")

        # Check the heal info
        heal_info1 = (redant.get_heal_info_summary(
                      self.server_list[0], self.vol_name))
        if heal_info1 is None:
            raise Exception("Failed to get the heal info summary.")

        # Bring bricks online
        if not (redant.bring_bricks_online(self.vol_name, self.server_list,
                offline_brick_list, True)):
            raise Exception("Failed to bring bricks: "
                            f"{offline_brick_list} online")

        # Issue heal
        if redant.trigger_heal_full(self.vol_name, self.server_list[0]):
            raise Exception("Unexpected: Able to trigger heal when self heal"
                            " daemon is not running")

        # Wait for 130 sec to heal
        if redant.monitor_heal_completion(self.server_list[0],
                                          self.vol_name, 130):
            raise Exception("Unexpected: Heal completed on volume")

        # Check the heal info
        heal_info = redant.get_heal_info_summary(self.server_list[0],
                                                 self.vol_name)
        if heal_info is None:
            raise Exception("Failed to get the heal info summary.")

        # Compare with heal pending with the files wrote
        for node in online_bricks:
            num_files_to_heal = int(heal_info[node]['numberOfEntries'])
            if num_files_to_heal < 100:
                raise Exception("Some of the files are healed from "
                                f"source bricks {node} where self heal"
                                "daemon is not running")

        # Unmount and Mount volume again as volume options were set
        # after mounting the volume
        for client in self.client_list:
            redant.volume_unmount(self.vol_name, self.mountpoint,
                                  client)
            redant.volume_mount(self.server_list[0], self.vol_name,
                                self.mountpoint, client)

        all_mounts_procs = []
        for mount_obj in self.mnt_list:
            cmd = (f"cd {mount_obj['mountpath']}; for i in `seq 1 5`; "
                   "do ls -l; cat *; stat *; sleep 5; done")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(all_mounts_procs, self.mnt_list):
            raise Exception("IO validation failed")

        # Wait for heal to complete
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name, 2400):
            raise Exception("Heal has not yet completed")
