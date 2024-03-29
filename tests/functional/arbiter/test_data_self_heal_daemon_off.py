"""
Copyright (C) 2020  Red Hat, Inc. <http://www.redhat.com>

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
    Arbiter Test cases related to
    healing in default configuration of the volume
"""
# disruptive;arb,dist-arb
# TODO: nfs

import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            if len(self.all_mounts_procs) > 0:
                ret = (self.redant.
                       wait_for_io_to_complete(self.all_mounts_procs,
                                               self.mounts))
                if not ret:
                    raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Description:
        - set the volume option
        "metadata-self-heal": "off"
        "entry-self-heal": "off"
        "data-self-heal": "off"
        - create IO
        - Get arequal before getting bricks offline
        - set the volume option
        "self-heal-daemon": "off"
        - bring down all bricks processes from selected set
        - Get areeual after getting bricks offline and compare with
        arequal before getting bricks offline
        - modify the data
        - bring bricks online
        - set the volume option
        "self-heal-daemon": "on"
        - check daemons and start healing
        - check if heal is completed
        - check for split-brain
        - add bricks
        - do rebalance
        - create 1k files
        - while creating files - kill bricks and bring bricks online one by one
        in cycle
        - validate IO
        """
        self.all_mounts_procs = []
        self.mounts = [{'client': self.client_list[0],
                        'mountpath': self.mountpoint}]

        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0],
                                  multi_option=True)

        # Creating files on client side
        proc = redant.create_files('1k', self.mountpoint,
                                   self.client_list[0], 100)

        self.all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # Get arequal before getting bricks offline
        arequals = redant.collect_mounts_arequal(self.mounts)
        result_before_offline = arequals[0][-1].split(':')[-1]

        # Setting options
        options = {"self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Select bricks to bring offline
        bricks_to_bring_offline = (redant.
                                   select_volume_bricks_to_bring_offline(
                                       self.vol_name, self.server_list[0]))

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name,
                                           bricks_to_bring_offline):
            raise Exception("Failed to bring "
                            f"{bricks_to_bring_offline} offline")

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f'Bricks {bricks_to_bring_offline}'
                            ' are not offline')

        # Get arequal after getting bricks offline
        arequals = redant.collect_mounts_arequal(self.mounts)
        result_after_offline = arequals[0][-1].split(':')[-1]

        # Checking arequals before bringing bricks offline
        # and after bringing bricks offline
        if result_after_offline != result_before_offline:
            raise Exception('Checksums before and after bringing'
                            ' bricks online are not equal')

        # Modify the data
        self.all_mounts_procs = []
        proc = redant.create_files('10k', self.mountpoint,
                                   self.client_list[0], 100)

        self.all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # Bring brick online
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_to_bring_offline)
        if not redant.are_bricks_online(self.vol_name,
                                        bricks_to_bring_offline,
                                        self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline}"
                            " are not online.")

        # Setting options
        options = {"self-heal-daemon": "on"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Wait for volume processes to be online
        if not redant.wait_for_volume_process_to_be_online(self.vol_name,
                                                           self.server_list[0],
                                                           self.server_list):
            raise Exception(f"Failed to wait for volume {self.vol_name} "
                            "processes to be online")

        # Verify volume's all process are online
        if not (redant.
                verify_all_process_of_volume_are_online(self.vol_name,
                                                        self.server_list[0])):
            raise Exception(f"Volume {self.vol_name} : All process"
                            " are not online")

        # Wait for self-heal-daemons to be online
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Either No self heal daemon process found")

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception("Heal is not started")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # is heal complete testing
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume in split-brain")

        # Add bricks
        if not (redant.
                expand_volume(self.server_list[0], self.vol_name,
                              self.server_list, self.brick_roots)):
            raise Exception("Failed to expamd volume")

        # Do rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        if not redant.wait_for_rebalance_to_complete(self.vol_name,
                                                     self.server_list[0]):
            raise Exception("Rebalance is not completed")

        # Create 1k files
        self.all_mounts_procs = []

        proc = redant.create_files('1k', self.mountpoint,
                                   self.client_list[0], 1000)

        self.all_mounts_procs.append(proc)

        # Kill all bricks in cycle
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        for brick in bricks_list:

            # Bring brick offline
            if not (redant.
                    bring_bricks_offline(self.vol_name, [brick])):
                raise Exception(f"Failed to bring {brick} offline")

            if not redant.are_bricks_offline(self.vol_name,
                                             [brick],
                                             self.server_list[0]):
                raise Exception(f"{brick} is still online")

            # Introducing 10 second sleep when brick is down
            sleep(10)

            # Bring brick online
            redant.bring_bricks_online(self.vol_name, self.server_list,
                                       [brick])
            if not redant.are_bricks_online(self.vol_name,
                                            [brick],
                                            self.server_list[0]):
                raise Exception(f"Bricks {[brick]}"
                                " are not online.")

            # Wait for volume processes to be online
            if not (redant.
                    wait_for_volume_process_to_be_online(self.vol_name,
                                                         self.server_list[0],
                                                         self.server_list)):
                raise Exception(f"Failed to wait for volume {self.vol_name} "
                                "processes to be online")

            # Verify volume's all process are online
            if not (redant.
                    verify_all_process_of_volume_are_online(
                        self.vol_name,
                        self.server_list[0])):
                raise Exception(f"Volume {self.vol_name} : All process"
                                " are not online")

            # Wait for self-heal-daemons to be online
            if not redant.is_shd_daemonized(self.server_list):
                raise Exception("Either No self heal daemon process found")

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")
