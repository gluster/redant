"""
Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    AFR Test cases related to healing in
    default configuration of the volume
"""

# disruptive;rep
# TODO cifs

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

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

    def _test_data_self_heal_command(self):
        """
        Test Data-Self-Heal (heal command)

        Description:
        - get the client side healing volume options and check
        if they have already been disabled by default
        NOTE: Client side healing has been disabled by default
        since GlusterFS 6.0
        "metadata-self-heal": "off"
        "entry-self-heal": "off"
        "data-self-heal": "off"
        - create IO
        - Get arequal before getting bricks offline
        - set the volume option
        "self-heal-daemon": "off"
        - bring down all bricks processes from selected set
        - Get arequal after getting bricks offline and compare with
        arequal before getting bricks offline
        - modify the data
        - bring bricks online
        - set the volume option "self-heal-daemon": "on"
        - check daemons and start healing
        - check if heal is completed
        - check for split-brain
        - create 5k files
        - while creating files - kill bricks and bring bricks online one by one
        in cycle
        - validate IO
        """
        self.io_validation_complete = True

        # Checking if Client side healing options are disabled by default
        options = ('cluster.metadata-self-heal',
                   'cluster.data-self-heal',
                   'cluster.entry-self-heal')
        options_dict = (self.redant.get_volume_options(self.vol_name,
                        node=self.server_list[0]))

        # validating options are off
        for opt in options:
            if options_dict[opt] != 'off (DEFAULT)':
                raise Exception("Options are not set to off")

        # Creating files on client side
        self.mounts = (self.
                       redant.es.get_mnt_pts_dict_in_list(self.vol_name))
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # Create files
            self.redant.logger.info("Starting IO on "
                                    f"{mount_obj['client']}:"
                                    f"{mount_obj['mountpath']}")
            proc = self.redant.create_files(num_files=100,
                                            fix_fil_size="1k",
                                            path=mount_obj['mountpath'],
                                            node=mount_obj['client'])
            self.all_mounts_procs.append(proc)
        self.io_validation_complete = False

        # Validate IO
        ret = self.redant.validate_io_procs(self.all_mounts_procs,
                                            self.mounts)
        if not ret:
            raise Exception("IO validation failed")
        self.io_validation_complete = True

        # Get arequal before getting bricks offline
        result_before_offline = (self.redant.
                                 collect_mounts_arequal(self.mounts))

        # Select bricks to bring offline and bring brick offline
        brick_list = (self.redant.
                      select_volume_bricks_to_bring_offline(
                          self.vol_name,
                          self.server_list[0]))
        if brick_list is None:
            raise Exception("Failed to select volume bricks to"
                            " bring offline")
        ret = self.redant.bring_bricks_offline(self.vol_name, brick_list)
        if not ret:
            raise Exception(f"{brick_list} still online.")

        if not self.redant.are_bricks_offline(self.vol_name,
                                              brick_list, self.server_list[0]):
            raise Exception(f"{brick_list} is not offline.")

        # Get arequal after getting bricks offline
        result_after_offline = (self.redant.
                                collect_mounts_arequal(self.mounts))

        # Checking arequals before bringing bricks offline
        # and after bringing bricks offline
        if result_before_offline != result_after_offline:
            raise Exception("Checksums before and after bringing "
                            "bricks offline are not equal")

        # Modify the data
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # Create files
            self.redant.logger.info("Modifying files on "
                                    f"{mount_obj['client']}:"
                                    f"{mount_obj['mountpath']}")
            proc = self.redant.create_files(num_files=100,
                                            fix_fil_size="10k",
                                            path=mount_obj['mountpath'],
                                            node=mount_obj['client'])
            self.all_mounts_procs.append(proc)
        self.io_validation_complete = False

        # Validate IO
        ret = self.redant.validate_io_procs(self.all_mounts_procs,
                                            self.mounts)
        if not ret:
            raise Exception("IO validation failed")
        self.io_validation_complete = True

        # Bring brick online
        if not self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                               brick_list):
            raise Exception("unable to bring "
                            f"{brick_list} online")

        # Wait for volume processes to be online
        if not (self.redant.wait_for_volume_process_to_be_online(
                self.vol_name, self.server_list[0],
                self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verify volume's all processes are online
        if not (self.redant.verify_all_process_of_volume_are_online(
                self.vol_name, self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Wait for self-heal-daemons to be online
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # Start healing
        if not self.redant.trigger_heal(self.vol_name,
                                        self.server_list[0]):
            raise Exception("Start heal failed")

        # Monitor heal completion
        if not (self.redant.monitor_heal_completion(
                self.server_list[0], self.vol_name)):
            raise Exception("Heal has not yet completed")

        # Check if heal is completed
        if not self.redant.is_heal_complete(self.server_list[0],
                                            self.vol_name):
            raise Exception("Heal not yet finished")

        # Check for split-brain
        if self.redant.is_volume_in_split_brain(self.server_list[0],
                                                self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Create 1k files
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # Create files
            self.redant.logger.info("Create more files on "
                                    f"{mount_obj['client']}:"
                                    f"{mount_obj['mountpath']}")
            proc = self.redant.create_files(num_files=1000,
                                            fix_fil_size="1k",
                                            path=mount_obj['mountpath'],
                                            node=mount_obj['client'])
            self.all_mounts_procs.append(proc)
        self.io_validation_complete = False

        # Kill all bricks in cycle
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        for brick in bricks_list:
            # Bring brick offline
            self.redant.bring_bricks_offline(self.vol_name, brick)
            if not self.redant.are_bricks_offline(self.vol_name, brick,
                                                  self.server_list[0]):
                raise Exception(f"Brick {brick} is not offline")

            # Bring brick online
            self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                            brick)

            # Wait for volume processes to be online
            if not (self.redant.wait_for_volume_process_to_be_online(
                    self.vol_name, self.server_list[0],
                    self.server_list)):
                raise Exception("Failed to wait for volume processes to "
                                "be online")

            # Verify volume's all processes are online
            if not (self.redant.verify_all_process_of_volume_are_online(
                    self.vol_name, self.server_list[0])):
                raise Exception("All process of volume are not online")

            # Wait for self-heal-daemons to be online
            if not self.redant.is_shd_daemonized(self.server_list):
                raise Exception("Self Heal Daemon process was still"
                                " holding parent process.")

        # Validate IO
        ret = self.redant.validate_io_procs(self.all_mounts_procs,
                                            self.mounts)
        if not ret:
            raise Exception("IO validation failed")
        self.io_validation_complete = True

    def _test_self_heal_50k_files_heal_default(self):
        """
        Test self-heal of 50k files by heal default
        Description:
        - bring down all bricks processes from selected set
        - create IO (50k files)
        - Get arequal before getting bricks online
        - check for daemons to come online
        - heal daemon should pick  up entries to heal automatically
        - check if heal is completed
        - check for split-brain
        - get arequal after getting bricks online and compare with
        arequal before getting bricks online
        """
        self.io_validation_complete = True

        # Select bricks to bring offline
        offline_bricks = (self.redant.select_volume_bricks_to_bring_offline(
                          self.vol_name, self.server_list[0]))

        # Bring brick offline
        self.redant.bring_bricks_offline(self.vol_name, offline_bricks)
        if not self.redant.are_bricks_offline(self.vol_name,
                                              offline_bricks,
                                              self.server_list[0]):
            raise Exception("Failed to bring down the bricks. Please "
                            "check the log file for more details.")

        # Creating files on client side
        self.mounts = (self.redant.es.
                       get_mnt_pts_dict_in_list(self.vol_name))

        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # Create 50k files
            self.redant.logger.info("Creating 5Ok files on "
                                    f"{mount_obj['client']}:"
                                    f"{mount_obj['mountpath']}")
            proc = self.redant.create_files(num_files=50000,
                                            fix_fil_size="1k",
                                            path=mount_obj['mountpath'],
                                            node=mount_obj['client'])
            self.all_mounts_procs.append(proc)
        self.io_validation_complete = False

        # Validate IO
        ret = self.redant.validate_io_procs(self.all_mounts_procs,
                                            self.mounts)
        if not ret:
            raise Exception("IO validation failed")
        self.io_validation_complete = True

        # Get arequal before getting bricks online
        result_before_online = (self.redant.
                                collect_mounts_arequal(self.mounts))

        # Bring brick online
        self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                        offline_bricks)

        # Wait for volume processes to be online
        if not (self.redant.wait_for_volume_process_to_be_online(
                self.vol_name, self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verify volume's all process are online
        if not (self.redant.verify_all_process_of_volume_are_online(
                self.vol_name, self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Wait for self-heal-daemons to be online
        if not self.redant.is_shd_daemonized(self.server_list):
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # Default Heal testing, wait for shd to pick up healing
        # Monitor heal completion
        if not (self.redant.monitor_heal_completion(
                self.server_list[0], self.vol_name, 3600)):
            raise Exception("Heal has not yet completed")

        # Check if heal is completed
        if not self.redant.is_heal_complete(self.server_list[0],
                                            self.vol_name):
            raise Exception("Heal not yet finished")

        # Check for split-brain
        if self.redant.is_volume_in_split_brain(self.server_list[0],
                                                self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequal after getting bricks online
        result_after_online = (self.redant.
                               collect_mounts_arequal(self.mounts))

        # Checking arequals before bringing bricks online
        # and after bringing bricks online
        if result_before_online != result_after_online:
            raise Exception("Checksums before and after bringing "
                            "bricks online are not equal")

    def run_test(self, redant):
        """
        1.Test Data-Self-Heal (heal command)
        2.Test self-heal of 50k files by heal default
        """
        self._test_data_self_heal_command()
        redant.logger.info("Data-Self-Heal check is successful")

        self._test_self_heal_50k_files_heal_default()
        redant.logger.info("self-heal of 50k files is successful")
