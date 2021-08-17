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
51 Franklin Street, Fifth Floor, Boston, MA 02110-131 USA.

Description:
    heal info completes when there is ongoing I/O and a lot of pending heals.
"""

# disruptive;dist-rep

import random
import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """Wait for IO, if the TC fails"""
        try:
            if self.io_validation_complete:
                if not self.redant.wait_for_io_to_complete(
                        self.list_of_io_processes, self.mounts):
                    raise Exception("Failed to wait for IO to finish")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _does_heal_info_complete_within_timeout(self, num_entries):
        """Check if heal info CLI completes within a specific timeout"""
        # We are just assuming 1 entry takes one second to process, which is
        # a very high number but some estimate is better than a random magic
        # value for timeout.
        timeout = num_entries * 1

        # heal_info_data = get_heal_info(self.server_list[0], self.vol_name)
        cmd = (f"timeout {timeout} gluster volume heal {self.vol_name} info")
        ret = self.redant.execute_abstract_op_node(cmd, self.server_list[0])
        if ret:
            return False
        return True

    def run_test(self, redant):
        """
        Testcase steps:
        1. Perform I/O on mounts
        2. While IO is going on, kill a brick of the replica.
        3. Wait for the IO to be over, resulting in pending heals.
        4. Get the approx. number of pending heals and save it
        5. Bring the brick back online.
        6. Trigger heal
        7. Run more I/Os with dd command
        8. Run heal info command and check that it completes successfully under
           a timeout that is based on the no. of heals in step 4.
        """
        self.io_validation_complete = False
        self.list_of_io_processes = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for count, mount in enumerate(self.mounts):
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      count, 2, 2, 2, 10,
                                                      mount['client'])
            self.list_of_io_processes.append(proc)
            self.io_validation_complete = True

        # Kill brick resulting in heal backlog.
        bricks_online = redant.get_online_bricks_list(self.vol_name,
                                                      self.server_list[0])
        if bricks_online is None:
            raise Exception("Unable to get online brick list")

        brick = random.choice(bricks_online)
        redant.bring_bricks_offline(self.vol_name, brick)

        if not redant.are_bricks_offline(self.vol_name, brick,
                                         self.server_list[0]):
            raise Exception(f"Brick {brick} is not offline")

        if not redant.validate_io_procs(self.list_of_io_processes,
                                        self.mounts):
            raise Exception("IO didn't complete or failed on client")
        self.io_validation_complete = False

        # Get approx. no. of entries to be healed.
        cmd = (f"gluster volume heal {self.vol_name} statistics heal-count | "
               "grep Number | awk '{sum+=$4} END {print sum/2}'")

        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        if ret['error_code'] != 0:
            raise Exception("Failed to get heal-count statistics")

        num_entries = int("".join(ret['msg']))

        # Restart the down bricks
        if not redant.bring_bricks_online(self.vol_name,
                                          self.server_list, brick):
            raise Exception(f"unable to bring {brick} online")

        # Trigger heal
        if not self.redant.trigger_heal(self.vol_name,
                                        self.server_list[0]):
            raise Exception("Starting heal failed")
        redant.logger.info("Index heal launched")

        cmd = (f"cd {self.mountpoint} ; "
               "for i in `seq 1 10` ; "
               "do dd if=/dev/urandom of=file_$i "
               "bs=1M count=100; done")

        redant.execute_command_async(cmd, self.client_list[0])

        # Get heal info
        ret = self._does_heal_info_complete_within_timeout(num_entries)
        if ret:
            raise Exception("Heal info timed out")
        redant.logger.info("Heal info completed succesfully")
