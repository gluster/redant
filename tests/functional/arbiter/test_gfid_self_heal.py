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
    Arbiter Test cases related to GFID self heal
"""
# disruptive;arb,dist-arb

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - Creating directory test_compilation
        - Write Deep directories and files
        - Get arequal before getting bricks offline
        - Select bricks to bring offline
        - Bring brick offline
        - Delete directory on mountpoint where data is writte
        - Create the same directory and write same data
        - Bring bricks online
        - Wait for volume processes to be online
        - Verify volume's all process are online
        - Monitor heal completion
        - Check for split-brain
        - Get arequal after getting bricks online
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []

        # Creating directory test_compilation
        redant.create_dir(self.mountpoint, 'test_gfid_self_heal',
                          self.client_list[0])

        # Write Deep directories and files
        count = 1
        for mount_obj in self.mounts:
            proc = (redant.
                    create_deep_dirs_with_files(
                        f'{mount_obj["mountpath"]}/dir1',
                        count, 2, 10, 5, 5,
                        mount_obj['client']))
            self.all_mounts_procs.append(proc)
            count += 10

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Get arequal before getting bricks offline
        result_before_offline = redant.collect_mounts_arequal(self.mounts)
        if result_before_offline is None:
            raise Exception('Failed to get arequal')

        # Select bricks to bring offline
        bricks_to_bring_offline = (redant.
                                   select_volume_bricks_to_bring_offline(
                                       self.vol_name, self.server_list[0]))
        if bricks_to_bring_offline is None:
            raise Exception("Failed to select bricks from volume")

        # Bring brick offline
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f'Bricks {bricks_to_bring_offline} '
                            'are not offline')

        # Delete directory on mountpoint where data is written
        # cmd = f'rm -rf -v {self.mountpoint}/test_gfid_self_heal'
        if not redant.rmdir(f'{self.mountpoint}/test_gfid_self_heal',
                            self.client_list[0], True):
            raise Exception("Failed to delete directory")

        # Create the same directory and write same data
        redant.create_dir(self.mountpoint, 'test_gfid_self_heal',
                          self.client_list[0])

        # Write the same files again
        self.all_mounts_procs = []
        count = 1
        for mount_obj in self.mounts:
            proc = (redant.
                    create_deep_dirs_with_files(
                        f'{mount_obj["mountpath"]}/dir1',
                        count, 2, 10, 5, 5,
                        mount_obj['client']))
            self.all_mounts_procs.append(proc)
            count += 10

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Bring bricks online
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_to_bring_offline, True)
        if not redant.are_bricks_online(self.vol_name, bricks_to_bring_offline,
                                        self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline}"
                            " are not online.")

        # Wait for volume processes to be online
        if not (redant
                .wait_for_volume_process_to_be_online(self.vol_name,
                                                      self.server_list[0],
                                                      self.server_list)):
            raise Exception(f"Failed to wait for volume {self.vol_name}"
                            " processes to be online")

        # Verify volume's all process are online
        if not (redant.
                verify_all_process_of_volume_are_online(self.vol_name,
                                                        self.server_list[0])):
            raise Exception(f"Volume {self.vol_name} : All process are "
                            "not online")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume in split-brain")

        # # Get arequal after getting bricks online
        result_after_online = redant.collect_mounts_arequal(self.mounts)
        if result_after_online is None:
            raise Exception('Failed to get arequal')
