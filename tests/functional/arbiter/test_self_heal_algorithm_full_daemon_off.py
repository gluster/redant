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
    TC to check heal when algorithm is set to "full" and self heal daemon
    is "off".
"""

# disruptive;arb,dist-arb
# TODO: NFS, CIFS
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        Test steps:
        1. Set the following options for the volume:
           "metadata-self-heal": "disable",
           "entry-self-heal": "disable",
           "data-self-heal": "disable",
           "data-self-heal-algorithm": "full",
           "self-heal-daemon": "off"
        2. Bring few bricks offline
        3. Check if the bricks are offline
        4. Start IO on mountpoint
        5. Validate the IO
        6. Collect mounts_arequal value
        7. Set self-heal-damon to ON
        8. Bring bricks online
        9. Monitor heal completion
        10. Compare the mounts-arequal before and after brick is online
        """
        # Setting volume option of self heal & algorithm
        options = {"metadata-self-heal": "disable",
                   "entry-self-heal": "disable",
                   "data-self-heal": "disable",
                   "data-self-heal-algorithm": "full",
                   "self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Select bricks to bring down
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Bring brick offline
        if not redant.bring_bricks_offline(self.vol_name,
                                           offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        # Validate if bricks are offline
        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Start IO on the mount point
        cmd = (f"cd {self.mountpoint}; for i in `seq 1 100` ;"
               "do dd if=/dev/urandom of=file$i bs=1M "
               "count=1;done")
        proc = redant.execute_command_async(cmd, self.client_list[0])

        # Validate IO
        mount_dict = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = self.redant.validate_io_procs(proc, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Collecting Arequal before bring the bricks up
        result_before = redant.collect_mounts_arequal(mount_dict)

        # Turning self heal daemon ON
        options = {"self-heal-daemon": "on"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Bring bricks online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick_list):
            raise Exception("Failed to bring bricks online")

        # Waiting for bricks to come online
        if not redant.wait_for_bricks_to_come_online(self.vol_name,
                                                     self.server_list,
                                                     offline_brick_list,
                                                     timeout=30):
            raise Exception("Bricks didn't come online")

        # Wait for self heal processes to come online
        if not (redant.wait_for_self_heal_daemons_to_be_online(self.vol_name,
                self.server_list[0])):
            raise Exception("Self-heal process are not online")

        # Verifying all bricks online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Wait for self-heal to complete
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # arequal after healing
        result_after = redant.collect_mounts_arequal(mount_dict)

        # Comparing the results
        if result_before != result_after:
            raise Exception("Arequals are not equal")
