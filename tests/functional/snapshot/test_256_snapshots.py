"""
 Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to validate creation of 256 snapshots
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
# TODO: NFS,CIFS
from time import sleep
from tests.d_parent_test import DParentTest


class TestValidateSnaps256(DParentTest):

    def run_test(self, redant):
        """
        * Perform some IO
        * Set snapshot config option snap-max-hard-limit to 256
        * Create 256 snapshots
        * Verify 256 created successfully
        * Create 257th snapshot - creation should fail as it will
          exceed the hard-limit
        * Verify snapshot list for 256 snapshots
        """
        self.all_mounts_procs = []
        self.snapshots = [(f"snap-test-validate-256-snapshots-{self.vol_name}"
                           f"-{i}")for i in range(0, 256)]

        # Start IO on all mounts
        cmd = ("python3 /tmp/file_dir_ops.py create_files -f 10 "
               f"--base-file-name firstfiles {self.mountpoint}")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        self.all_mounts_procs.append(proc)

        # Wait for IO to complete
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on the clients")

        # Perform stat on all the files/dirs created
        redant.get_mounts_stat(self.mounts)

        # Set config option snap-max-hard-limit to 256
        # This is to make sure to override
        max_hard_limit = {'snap-max-hard-limit': '256'}
        redant.set_snap_config(max_hard_limit, self.server_list[0],
                               self.vol_name)

        # Create 256 snapshots
        for snapname in self.snapshots:
            redant.snap_create(self.vol_name, snapname, self.server_list[0])
            sleep(1)

        # Validate snapshot list for 256 snapshots
        snap_list = redant.get_snap_list(self.server_list[0])
        if len(snap_list) != 256:
            raise Exception("Failed: Number of snapshots "
                            f"is not consistent for volume {self.vol_name}")

        # Validate snapshot existence using snap-name
        for snapname in self.snapshots:
            if snapname not in snap_list:
                raise Exception(f"Failed: Snapshot {snapname} not found")

        # Try to exceed snap-max-hard-limit by creating 257th snapshot
        snap_257 = f"snap-test-validate-256-snapshots-{self.vol_name}-257"
        ret = redant.snap_create(self.vol_name, snap_257, self.server_list[0],
                                 excep=False)
        if ret['error_code'] == 0:
            raise Exception(f"Unexpected: Successfully created {snap_257} for"
                            f" volume {self.vol_name}")

        # Validate snapshot list for 256 snapshots
        snap_list = redant.get_snap_list(self.server_list[0])
        if len(snap_list) != 256:
            raise Exception("Failed: Number of snapshots "
                            f"is not consistent for volume {self.vol_name}")
