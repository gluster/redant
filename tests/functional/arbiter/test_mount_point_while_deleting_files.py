"""
 Copyright (C) 2016-2020 Red Hat, Inc. <http://www.redhat.com>

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
    TC to check files are deleted from mounpoint properly
"""

# disruptive;
from tests.d_parent_test import DParentTest


class TestVolumeSetDataSelfHealTests(DParentTest):

    def run_test(self, redant):
        """
        - create two volumes with arbiter1 and mount it on same client
        - create IO
        - start deleting files from both mountpoints
        - kill brick from one of the node
        - Check if all the files are deleted from the mount point
        from both the servers
        """
        # Create and start 2 arbiter 1 volumes
        conf_hash = self.vol_type_inf['arb']
        for i in range(1, 3):
            redant.setup_volume(f"arb-volume{i}", self.server_list[0],
                                conf_hash, self.server_list,
                                self.brick_roots)

            # Mount the volumes on same client
            redant.execute_abstract_op_node(f"mkdir -p /mnt/arb-volume{i}",
                                            self.client_list[0])

            redant.volume_mount(self.server_list[0], f"arb-volume{i}",
                                f"mnt/arb-volume{i}", self.client_list[0])

        # create files on all mounts
        procs_list = []
        mount_dict = []
        for i in range(1, 3):
            proc = redant.create_files("1M", f"/mnt/arb-volume{i}",
                                       self.client_list[0], 100)
            procs_list.append(proc)
            mount_dict.append({
                "client": self.client_list[0],
                "mountpath": f"/mnt/arb-volume{i}"
            })

        # Validate IO
        ret = self.redant.validate_io_procs(procs_list, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # select bricks to bring offline
        volume_list = redant.get_volume_list(self.server_list[0])
        for volname in volume_list:
            brick_list = (redant.select_volume_bricks_to_bring_offline(
                          volname, self.server_list[0]))

            # bring bricks offline
            if not redant.bring_bricks_offline(volname,
                                               brick_list):
                raise Exception("Failed to bring down the bricks. Please "
                                "check the log file for more details.")

        # delete files on all mounts
        procs_list = []
        for i in range(1, 3):
            cmd = "rm -rf *"
            proc = redant.execute_command_async(cmd, self.client_list[0])
            procs_list.append(proc)

        # Validate IO
        ret = self.redant.validate_io_procs(procs_list, mount_dict)
        if not ret:
            raise Exception("IO validation failed")
