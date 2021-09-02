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
    Test Cases in this module tests the creation of snapshot and mounting
    that snapshot in the client.
"""

# disruptive;rep,dist-rep,disp,dist,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestSnapMountSnapshot(DParentTest):

    def terminate(self):
        """
        Unmount the snap mount, if mounted
        """
        try:
            if self.is_mounted:
                cmd = f"umount {self.mpoint}"
                self.redant.execute_abstract_op_node(cmd, self.client_list[0],
                                                     False)
                cmd = f"rm -rf {self.mpoint}"
                self.redant.execute_abstract_op_node(cmd, self.client_list[0],
                                                     False)
        except Exception as e:
            tb = traceback.format_exc()
            self.redant.logger.error(e)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Mount the snap volume
        * Create volume, FUSE mount the volume
        * perform I/O on mount points
        * Creating snapshot and activate snapshot
        * FUSE mount the snapshot created
        * Perform I/O on mounted snapshot
        * I/O should fail
        """
        self.is_mounted = False
        self.mpoint = "/mnt/snap1"
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # starting I/O
        all_mounts_procs = []
        for mount_obj in self.mounts:
            proc = redant.create_files("1k", mount_obj['mountpath'],
                                       mount_obj['client'], 10, 'file')
            all_mounts_procs.append(proc)

        # Validate I/O
        if not redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO failed.")

        # Creating snapshot
        redant.snap_create(self.vol_name, "snap1", self.server_list[0])

        # Activating snapshot
        redant.snap_activate("snap1", self.server_list[0])

        # FUSE mount snap1 snapshot
        cmd = f"mkdir -p  {self.mpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        cmd = (f"mount.glusterfs {self.server_list[0]}:/snaps/snap1/"
               f"{self.vol_name} {self.mpoint}")
        redant.execute_abstract_op_node(cmd, self.client_list[0])
        self.is_mounted = True

        # starting I/O
        all_mounts_procs = []
        for mount_obj in self.mounts:
            proc = redant.create_files("1k", mount_obj['mountpath'],
                                       mount_obj['client'], 10, 'newfile')
            all_mounts_procs.append(proc)

        # Validate I/O
        if not redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO failed.")

        # start I/O
        self.mounts1 = [{
            "client": self.client_list[0],
            "mountpath": self.mpoint
        }]
        all_mounts_procs = []
        for mount_obj in self.mounts1:
            proc = redant.create_files("1k", mount_obj['mountpath'],
                                       mount_obj['client'], 10, 'file')
            all_mounts_procs.append(proc)

        # Validate I/O
        if redant.validate_io_procs(all_mounts_procs, self.mounts1):
            raise Exception("Unexpected: IO successfull.")
