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
    TCs in this module tests the creation of clone from snapshot of volume.
"""

# disruptive;rep,dist,disp,dist-rep,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestSnapshotCloneDeleteMultiple(DParentTest):

    def terminate(self):
        """
        Disable activate-on-create option in snapshot config
        """
        try:
            option = {'activate-on-create': 'disable'}
            self.redant.set_snap_config(option, self.server_list[0])

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _io_operation(self, name):
        """
        Perform IO and validate it
        """
        # Perform I/O
        all_mounts_procs = []
        for mount_obj in self.mounts:
            # Create files
            proc = self.redant.create_files('1k', mount_obj['mountpath'],
                                            mount_obj['client'], 100, name)
            all_mounts_procs.append(proc)

        # Validate IO
        if not self.redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")

    def _create_and_clone_snap(self, value, snap, clone, counter):
        """
        Create snaps, clone them and start the cloned snap volume
        """
        # Creating snapshots
        for snap_count in value:
            self.redant.snap_create(self.vol_name, f"snap{snap_count}",
                                    self.server_list[0])

        # Validate snapshot list
        ret = self.redant.snap_list(self.server_list[0])
        if int(ret['msg']['snapList']['count']) != counter:
            raise Exception("Failed to validate snapshots with"
                            "expected number of snapshots")

        if counter == 40:
            return 0

        # Creating a Clone of snapshot:
        self.redant.snap_clone(snap, clone, self.server_list[0])

        # Start cloned volumes
        self.redant.volume_start(clone, self.server_list[0])

        # log Cloned Volume information
        if not self.redant.log_volume_info_and_status(self.server_list[0],
                                                      clone):
            raise Exception(f"Failed to Log Info, Status of Volume {clone}")

        return counter+10

    def _mount_clone_and_io(self, clone, mpoint):
        """
        Mount snapshot clones on client and validate
        """
        # Create mountpoint on client
        self.redant.execute_abstract_op_node(f"mkdir -p {mpoint}",
                                             self.client_list[0])

        # Mounting a volume
        self.redant.volume_mount(self.server_list[0], clone, mpoint,
                                 self.client_list[0])

        # Checking volume mounted or not
        if not self.redant.is_mounted(clone, mpoint, self.client_list[0],
                                      self.server_list[0]):
            raise Exception(f"Volume not mounted on mount point: {mpoint}")

    def run_test(self, redant):
        """
        Steps:
        1. create and mount volume
        2. Create 20 snapshots
        3. Clone one of the snapshot
        4. mount the clone volume
        5. Perform I/O on mounts
        6. Create 10 more snapshots
        7. create Clone volume from latest snapshot
           and Mount it
        8. Perform I/O
        9. Create 10 more snapshot
        10. Validate total number of
            snapshots created.
        11. Delete all created snapshots.
        """
        self.snap1 = "snap1"
        self.snap2 = "snap21"
        self.clone1 = "clone1"
        self.clone2 = "clone2"
        self.mpoint1 = "/mnt/clone1"
        self.mpoint2 = "/mnt/clone2"

        # Enable Activate on create
        option = {'activate-on-create': 'enable'}
        redant.set_snap_config(option, self.server_list[0])

        value1 = list(range(0, 20))
        value2 = list(range(20, 30))
        value3 = list(range(30, 40))
        # Clone and start clone1
        ret1 = self._create_and_clone_snap(value1, self.snap1, self.clone1,
                                           counter=20)
        if ret1 != 30:
            raise Exception("Failed to create and clone snap")

        # Mount clone1
        self._mount_clone_and_io(self.clone1, self.mpoint1)

        # Perform IO on mountpoint of clone1
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mpoint1
        }
        self._io_operation("first")

        # Clone and start clone2
        ret3 = self._create_and_clone_snap(value2, self.snap2, self.clone2,
                                           ret1)
        if ret3 != 40:
            raise Exception("Failed to create and clone snap")

        # Mount clone2
        self._mount_clone_and_io(self.clone2, self.mpoint2)

        # Perform IO on mountpoint of clone1
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mpoint2
        }
        self._io_operation("second")

        # Create 10 more snapshots
        ret1 = self._create_and_clone_snap(value3, self.snap2, self.clone2,
                                           ret3)
        if ret1 != 0:
            raise Exception("Failed to create snapshots")
