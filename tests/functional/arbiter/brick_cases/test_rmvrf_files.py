"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check remove files with -rfv option on mountpoint after
    killing a brick process
"""

# disruptive;arb,dist-arb
# TODO: NFS,CIFS
import traceback
from tests.d_parent_test import DParentTest


class TestRmrfMount(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if it TC fails in between
        """
        try:
            if not self.io_validation_complete:
                if not self.redant.wait_for_io_to_complete(self.proc_list,
                                                           self.mounts):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Description:-
        - Create files on mount point
        - Kill one brick from volume
        - rm -rfv on mount point
        - bring bricks online
        - wait for heals
        """
        # IO on the mount point
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.proc_list = []
        self.io_validation_complete = False
        counter = 0
        for mount in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 35, 5, 5,
                                                      mount['client'])
            self.proc_list.append(proc)
            counter += 10

        # Select bricks to bring offline
        offline_brick_list = (redant.select_volume_bricks_to_bring_offline(
                              self.vol_name, self.server_list[0]))

        # Killing one brick from the volume set
        if not redant.bring_bricks_offline(self.vol_name, offline_brick_list):
            raise Exception("Failed to bring bricks offline")

        # Validate if bricks are offline
        if not redant.are_bricks_offline(self.vol_name, offline_brick_list,
                                         self.server_list[0]):
            raise Exception(f"Bricks {offline_brick_list} are not offline")

        # Validate IO
        ret = self.redant.validate_io_procs(self.proc_list, self.mounts)
        if not ret:
            raise Exception("IO validation failed")
        self.io_validation_complete = True

        # Checking volume status
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed for "
                            f"volume {self.vol_name}")

        # Removing files from the mount point when one brick is down
        mountpoint = self.mounts[0]['mountpath']
        client = self.mounts[0]['client']
        cmd = f"rm -rfv {mountpoint}/*"
        redant.execute_abstract_op_node(cmd, client)

        # Bringing bricks online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          offline_brick_list):
            raise Exception("Failed to bring bricks online")

        # Check if bricks are online
        if not redant.are_bricks_online(self.vol_name, offline_brick_list,
                                        self.server_list[0]):
            raise Exception("Bricks are not online")

        # Monitoring heals on the volume
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # List all files and dirs created
        if not redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to list all files and dirs")
