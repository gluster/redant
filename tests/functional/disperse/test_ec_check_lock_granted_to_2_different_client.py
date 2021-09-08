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
    Add test to verify lock behaviour from 2 diff clients
"""

# disruptive;disp,dist-disp

import time
import itertools
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    @DParentTest.setup_custom_enable
    def setup_test(self):
        # Check server requirements
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=2)

        # Create and start the volume
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node("mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def run_test(self, redant):
        """
        - Create disperse volume and mount it to 2 clients`
        - Create file from 1 client on mount point
        - Take lock from client 1 => Lock is acquired
        - Try taking lock from client 2=> Lock is blocked (as already
          being taken by client 1)
        - Release lock from client1=> Lock is released
        - Take lock from client2
        - Again try taking lock from client 1
        - verify test with once, by disabling eagerlock and other eager lock
          and once by leaving eager and other eagerlock enabled(by default)
        """
        # Create a file on client 1
        cmd = f'touch {self.mountpoint}/test_file'
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Verifying OCL as ON
        option_dict = (redant.get_volume_options(self.vol_name,
                       'disperse.optimistic-change-log', self.server_list[0]))
        if option_dict['disperse.optimistic-change-log'].split()[0] != 'on':
            raise Exception("optimistic-change-log is not ON for volume")

        # Repeat the test with eager-lock and other-eager-lock 'on' & 'off'
        for lock_status in ('on', 'off'):
            options = {'disperse.eager-lock': lock_status,
                       'disperse.other-eager-lock': lock_status}
            redant.set_volume_options(self.vol_name, options,
                                      self.server_list[0], True)

            # Repeat the test for both the combinations of clients
            for client_1, client_2 in list(itertools.permutations(
                    [self.client_list[0], self.client_list[1]], r=2)):
                # Get lock to file from one client
                lock_cmd = ("python3 /usr/share/redant/script/file_lock.py "
                            f"-f {self.mountpoint}/test_file -t 30")
                proc = redant.execute_command_async(lock_cmd, client_1)
                time.sleep(5)

                # As the lock is been acquired by one client,
                # try to get lock from the other
                ret = redant.execute_abstract_op_node(lock_cmd, client_2,
                                                      False)
                if ret['error_code'] == 0:
                    raise Exception(f"Unexpected: {client_2} acquired the "
                                    f"lock before been released by {client_1}")

                # Wait for first client to release the lock.
                ret = redant.wait_till_async_command_ends(proc)
                if ret['error_code'] != 0:
                    raise Exception("File lock process failed on {client_1}")

                # Try taking the lock from other client and releasing it
                lock_cmd = ("python3 /usr/share/redant/script/file_lock.py "
                            f"-f {self.mountpoint}/test_file -t 1")
                proc = redant.execute_command_async(lock_cmd, client_2)
                time.sleep(5)

                ret = redant.wait_till_async_command_ends(proc)
                if ret['error_code'] != 0:
                    raise Exception(f"Unexpected: {client_2} can not acquire "
                                    "the lock even after its been "
                                    f"released by {client_1}")
