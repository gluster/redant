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
"""

# disruptive;dist,dist-rep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def _create_file_and_hold_lock(self):
        """ Creates a file and holds lock on the file created"""
        cmd = (f"cd {self.mountpoint}; dd if=/dev/zero of=test_file "
               "bs=10M count=1;")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Acquire lock to the file created
        self.proc = self.redant.execute_command_async(self.lock_cmd,
                                                      self.client_list[0])

    def _expand_volume_and_verify_rebalance(self):
        """ Expands the volume, trigger rebalance and verify file is copied"""

        # Expand the volume
        if not (self.redant.expand_volume(self.server_list[0], self.vol_name,
                self.server_list, self.brick_roots)):
            raise Exception("Failed to expand volume")

        # Trigger rebalance and wait for it to complete
        self.redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        if not (self.redant.wait_for_rebalance_to_complete(self.vol_name,
                                                           self.server_list[0],
                                                           timeout=1200)):
            raise Exception("Rebalance operation has not yet completed.")

    def _verify_file_lock(self):
        """ Verifies file lock on file before been released by 1st program"""

        ret = self.redant.execute_abstract_op_node(self.lock_cmd,
                                                   self.client_list[0],
                                                   False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Another program acquired the "
                            "lock before been released by 1st one")

        # Wait till the lock is been released
        ret = self.redant.wait_till_async_command_ends(self.proc)
        if ret['error_code'] != 0:
            raise Exception("File lock process failed.")

    def run_test(self, redant):
        """
        Steps:
        1. Create a distributed or distributed-replicate volume and
           populate some data
        2. Hold exclusive lock on a file (can use flock)
        3. Add-brick and rebalance (make sure this file gets migrated)
        4. Again from another program try to hold exclusive lock on this file
        """
        # Create a File
        self.lock_cmd = ("python3 /usr/share/redant/script/file_lock.py "
                         f"-f {self.mountpoint}/test_file -t 200")

        self._create_file_and_hold_lock()

        # Expand the volume
        self._expand_volume_and_verify_rebalance()

        # Try getting lock to the file while the lock is still held by another
        self._verify_file_lock()
        redant.logger.info("TC succecful to check Lock can't be "
                           "acquired before being released")
