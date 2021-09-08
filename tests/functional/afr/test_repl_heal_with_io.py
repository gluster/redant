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
    TC to check heal on replicate volume with IO
"""

# disruptive;arb,dist-arb,rep,dist-rep
from copy import deepcopy
from random import choice
from time import sleep, time
import traceback
from tests.d_parent_test import DParentTest


class TestHealWithIO(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        if self.volume_type.find("dist") >= 0:
            conf_hash['dist_count'] = 6

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")

        # Single mountpoint is enough for all tests
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0],
                                 self.vol_name,
                                 self.mountpoint, self.client_list[0])

        self.file_path = f"{self.mountpoint}/test_file"
        self._io_cmd = ('cat /dev/urandom | tr -dc [:space:][:print:] | '
                        'head -c {} ')

        # IO has to run for longer length for covering two scenarios in arbiter
        # volume type
        self.io_time = 600 if self.volume_type.find('arb') >= 0 else 300
        self.proc = []

    def terminate(self):
        """
        Wait for IO to complete if the TC fails early
        """
        try:
            if self.proc:
                self.mounts = {
                    "client": self.client_list[0],
                    "mountpath": self.mountpoint
                }
                ret = self.redant.wait_for_io_to_complete([self.proc],
                                                          self.mounts)
                if not ret:
                    raise Exception("Wait for IO completion failed on client")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _validate_heal(self, timeout=8):
        """
        Validates `heal info` command returns in less than `timeout` value
        """
        start_time = time()
        ret = self.redant.get_heal_info(self.server_list[0], self.vol_name)
        end_time = time()
        if ret is None:
            raise Exception("Unable to query heal info status")
        if end_time - start_time >= timeout:
            raise Exception("Query of heal info of volume took more than"
                            f" {timeout} seconds")

    def _validate_io(self, delay=5):
        """
        Validates IO was happening during main test, measures by looking at
        time delay between issue and return of `async_communicate`
        """
        start_time = time()
        ret = self.redant.wait_till_async_command_ends(self.proc)
        end_time = time()
        if ret['error_code'] != 0:
            raise Exception("IO failed to complete with error "
                            f"{ret['error_msg']}")

        if end_time - start_time <= delay:
            raise Exception('Unable to validate IO was happening during main'
                            ' test')
        self.proc = ''

    def _bring_brick_offline(self, bricks_list, arb_brick=False):
        """
        Bring arbiter brick offline if `arb_brick` is true else one of data
        bricks will be offline'd
        """
        if arb_brick:
            # Pick only `arbiter` brick
            off_brick, b_type = [bricks_list[-1]], 'arbiter'
        elif not arb_brick and self.volume_type.find('repl') >= 0:
            # Should pick all bricks if voltype is `replicated`
            off_brick, b_type = bricks_list, 'data'
        else:
            # Pick up only `data` brick
            off_brick, b_type = bricks_list[:-1], 'data'

        ret = self.redant.bring_bricks_offline(self.vol_name,
                                               choice(off_brick))
        if not ret:
            raise Exception(f"Unable to bring `{b_type}` brick offline")

    def _get_hashed_subvol_index(self, subvols):
        """
        Return `index` of hashed_volume from list of subvols
        """
        index = 0
        if self.volume_type.find('dist') >= 0:
            name = self.file_path.rsplit('/', 1)[1]
            hashed_subvol, index = self.redant.find_hashed_subvol(subvols, '',
                                                                  name)
            if hashed_subvol is None:
                raise Exception('Unable to find hashed subvolume')

        return index

    def _validate_brick_down_scenario(self, validate_heal=False,
                                      monitor_heal=False):
        """
        Refactor of common steps across volume type for validating brick down
        scenario
        """
        if validate_heal:
            # Wait for ample amount of IO to be written to file
            sleep(180)

            # Validate heal info shows o/p and exit in <8s
            self._validate_heal()

        # Force start volume and verify all process are online
        self.redant.volume_start(self.vol_name, self.server_list[0],
                                 force=True)

        if not (self.redant.wait_for_volume_process_to_be_online(
                self.vol_name, self.server_list[0], self.server_list)):
            raise Exception('Not able to confirm all process of volume are'
                            ' online')

        if monitor_heal:
            # Wait for IO to be written to file
            sleep(30)

            # Monitor heal and validate data was appended successfully to file
            if not self.redant.monitor_heal_completion(self.server_list[0],
                                                       self.vol_name):
                raise Exception('Self heal is not completed post brick '
                                'online')

    def _perform_heal_append_scenario(self):
        """
        Refactor of common steps in `entry_heal` and `data_heal` tests
        """
        # Find hashed subvol of the file with IO
        subvols = self.redant.get_subvols(self.vol_name, self.server_list[0])
        index = self._get_hashed_subvol_index(subvols)

        # Bring down one of the `data` bricks of hashed subvol
        self._bring_brick_offline(bricks_list=subvols[index])

        cmd = f"{self._io_cmd.format('1G')} >> {self.file_path}"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Start volume and verify all process are online
        self._validate_brick_down_scenario()

        # Start conitnuous IO and monitor heal completion
        cmd = (f"count={self.io_time}; while [ $count -gt 1 ]; "
               f"do {self._io_cmd.format('1M')} >> {self.file_path}; sleep 1;"
               " ((count--)); done;")
        self.proc = self.redant.execute_command_async(cmd,
                                                      self.client_list[0])
        self._validate_brick_down_scenario(monitor_heal=True)

        # Bring down `arbiter` brick and perform validation
        if self.volume_type.find('arb') >= 0:
            self._bring_brick_offline(bricks_list=subvols[index],
                                      arb_brick=True)
            self._validate_brick_down_scenario(monitor_heal=True)

        self._validate_io()

    def run_test(self, redant):
        """
        Test 1: test_heal_info_with_io
        Description: Validate heal info command with IO

        Steps:
        - Create and mount a 6x3 replicated volume
        - Create a file and perform IO continuously on this file
        - While IOs are happening issue `heal info` command and validate o/p
          not taking much time
        """
        cmd = ("count=90; while [ $count -gt 1 ]; do "
               f"{self._io_cmd.format('5M')} >> {self.file_path}; sleep 1;"
               " ((count--)); done;")
        self.proc = redant.execute_command_async(cmd, self.client_list[0])

        # Wait for IO to be written to file
        sleep(30)

        # Validate heal info shows o/p and exit in <5s
        self._validate_heal()

        # Validate IO was happening
        self._validate_io()
        redant.logger.info("Test heal info with IO is complete")

        """
        Test 2: test_heal_info_with_io_and_brick_down
        Description: Validate heal info command with IO and brick down

        Steps:
        - Create and mount a 6x3 replicated volume
        - Create a file and perform IO continuously on this file
        - While IOs are happening, bring down one of the brick where the file
          is getting hashed to
        - After about a period of ~5 min issue `heal info` command and
          validate o/p not taking much time
        - Repeat the steps for arbiter on bringing arbiter brick down
        """
        cmd = (f"count={self.io_time}; while [ $count -gt 1 ]; do "
               f"{self._io_cmd.format('5M')} >> {self.file_path}; sleep 1;"
               " ((count--)); done;")
        self.proc = redant.execute_command_async(cmd, self.client_list[0])

        # Wait for IO to be written to file
        sleep(30)

        # Find hashed subvol of the file with IO
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        index = self._get_hashed_subvol_index(subvols)

        # Bring down one of the `data` bricks of hashed subvol
        self._bring_brick_offline(bricks_list=subvols[index])

        # Validate heal and bring volume online
        self._validate_brick_down_scenario(validate_heal=True)

        # Bring down `arbiter` brick and perform validation
        if self.volume_type.find('arb') >= 0:
            self._bring_brick_offline(bricks_list=subvols[index],
                                      arb_brick=True)

            # Validate heal and bring volume online
            self._validate_brick_down_scenario(validate_heal=True)

        self._validate_io()
        redant.logger.info("Test heal info with IO and brick down completed")

        # Create, start and mount volume for rest of the tests
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        self.vol_name = f"{self.vol_name}-1"
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")

        # Single mountpoint is enough for all tests
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0],
                                 self.vol_name,
                                 self.mountpoint, self.client_list[0])

        """
        Test 3: test_data_heal_on_file_append
        Description: Validate appends to a self healing file (data heal check)

        Steps:
        - Create and mount a 1x3 replicated volume
        - Create a file of ~ 1GB from the mount
        - Bring down a brick and write more data to the file
        - Bring up the offline brick and validate appending data to the file
          succeeds while file self heals
        - Repeat the steps for arbiter on bringing arbiter brick down
        """
        cmd = f"{self._io_cmd.format('1G')} >> {self.file_path};"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Perform `data_heal` test
        self._perform_heal_append_scenario()
        redant.logger.info("Test data heal on file append is complete")

        """
        Test 4: test_entry_heal_on_file_append
        Description: Validate appends to a self healing file (entry heal check)

        Steps:
        - Create and mount a 1x3 replicated volume
        - Bring down a brick and write data to the file
        - Bring up the offline brick and validate appending data to the file
          succeeds while file self heals
        - Repeat the steps for arbiter on bringing arbiter brick down
        """

        # Perform `entry_heal` test
        self._perform_heal_append_scenario()
        redant.logger.info("Test entry heal on file append is complete")
