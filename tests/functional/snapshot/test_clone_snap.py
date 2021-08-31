"""
 Copyright (C) 2016-2017  Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module tests the creation of clone from snapshot
    of one volume.
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
# TODO: NFS,CIFS
from tests.d_parent_test import DParentTest


class TestCloneSnapshot(DParentTest):

    def run_test(self, redant):
        """
        * Create and Mount the volume
        * Enable some volume options
        * Creating 2 snapshots and activate
        * reset the volume
        * create a clone of snapshots created
        * Mount both the clones
        * Perform I/O on mount point
        * Check volume options of cloned volumes
        * Create snapshot of the cloned snapshot volume
        * cleanup snapshots and volumes
        """
        # Enabling Volume options on the volume and validating
        options = {"features.uss": "enable"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Validate feature.uss enabled or not
        option = "features.uss"
        ret = redant.get_volume_options(self.vol_name, option,
                                        self.server_list[0])
        if ret['features.uss'] != 'enable':
            raise Exception("Failed to validate volume options")

        # Creating snapshot
        for snap_count in range(0, 2):
            redant.snap_create(self.vol_name, f"snap{snap_count}",
                               self.server_list[0])

        # Activating snapshot
        for snap_count in range(0, 2):
            redant.snap_activate(f"snap{snap_count}", self.server_list[0])

        # Reset volume:
        redant.volume_reset(self.vol_name, self.server_list[0])

        # Validate feature.uss enabled or not
        option = "features.uss"
        ret = redant.get_volume_options(self.vol_name, option,
                                        self.server_list[0])
        if ret['features.uss'] != 'off':
            raise Exception("Failed to validate volume options")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("Few process after volume start are offline for "
                            f"volume: {self.vol_name}")

        # Creating and starting a Clone of snapshot
        for clone_count in range(0, 2):
            redant.snap_clone(f"snap{clone_count}", f"clone{clone_count}",
                              self.server_list[0])
            redant.volume_start(f"clone{clone_count}", self.server_list[0])

        # Validate Volume start of cloned volume
        for clone_count in range(0, 2):
            vol_info = redant.get_volume_info(self.server_list[0],
                                              f"clone{clone_count}")
            if vol_info[f"clone{clone_count}"]['statusStr'] != 'Started':
                raise Exception("Failed to get volume info for "
                                f"clone{clone_count}")

        # Validate feature.uss enabled or not
        option = "features.uss"
        for clone_count in range(0, 2):
            ret = redant.get_volume_options(f"clone{clone_count}", option,
                                            self.server_list[0])
        if ret['features.uss'] != 'enable':
            raise Exception("Failed to validate volume options")

        # Mount both the cloned volumes
        for mount_obj in range(0, 2):
            self.mpoint = f"/mnt/clone{mount_obj}"
            cmd = f"mkdir -p  {self.mpoint}"
            redant.execute_abstract_op_node(cmd, self.client_list[0])
            redant.volume_mount(self.server_list[0], f"clone{mount_obj}",
                                self.mpoint, self.client_list[0])

        # Perform I/O on mount
        all_mounts_procs = []
        for mount_obj in range(0, 2):
            cmd = (f"cd /mnt/clone{mount_obj}/; for i in {{1..10}};"
                   "do touch file$i; done; cd;")
            redant.execute_abstract_op_node(cmd, self.client_list[0])

        # create snapshot
        redant.snap_create("clone0", "snap2", self.server_list[0])
        redant.snap_create("clone1", "snap3", self.server_list[0])

        # Listing all Snapshots present
        redant.snap_list(self.server_list[0])
