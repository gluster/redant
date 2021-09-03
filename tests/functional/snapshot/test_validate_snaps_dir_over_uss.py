"""
 Copyright (C) 2017-2020 Red Hat, Inc. <http://www.redhat.com>

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
    The purpose of this test case is to ensure that USS validation.
    Where .snaps folder is only readable and is listing all the snapshots
    and it's content. Also ensures that deactivated snapshot doesn't
    get listed.
"""

# disruptive;rep,dist-rep,disp,dist,dist-disp
# TODO: NFS,CIFS
from tests.d_parent_test import DParentTest


class TestValidateUss(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        - Run IOs on mount and take 2 snapshot.
        - Activate 1 snapshot and check directory listing.
        - Try to write to .snaps should not allow.
        - Try listing the other snapshot should fail.
        """
        # Run IOs
        counter = 1
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 2, 2, 2,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter += 10

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed.")

        # get the snapshot list.
        snap_list = redant.get_snap_list(self.server_list[0])
        if len(snap_list) != 0:
            raise Exception(f"Unexpected: {snap_list} snapshots present")

        # Create 2 snapshot
        for snap_num in range(0, 2):
            redant.snap_create(self.vol_name, f"snap-{snap_num}",
                               self.server_list[0])

        # Activate snap-0
        redant.snap_activate("snap-0", self.server_list[0])

        # Enable USS for volume
        redant.enable_uss(self.vol_name, self.server_list[0])

        # Validate uss enabled
        if not redant.is_uss_enabled(self.vol_name, self.server_list[0]):
            raise Exception(f"USS is not enabled in {self.server_list[0]}")

        # list activated snapshots directory under .snaps
        for mount_obj in self.mounts:
            ret = redant.uss_list_snaps(mount_obj['client'],
                                        mount_obj['mountpath'])
            validate_dir = "".join(ret['msg']).strip().split('\n')
            if "snap-0" not in validate_dir:
                raise Exception("Failed to validate snap-0 under .snaps"
                                " directory")
            if "snap-1" in validate_dir:
                raise Exception("Unexpected: Successfully listed snap-1 under"
                                " .snaps directory")

        # start I/0 ( write and read )
        all_mounts_procs = []
        for mount_obj in self.mounts:
            pc = redant.create_files('1k',
                                     f"{mount_obj['mountpath']}/.snaps/abc/",
                                     mount_obj['client'], 10, 'file')
            all_mounts_procs.append(pc)

        # IO should fail
        if redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("Unexpected: IO successfull.")

        # validate snap-0 present in mountpoint
        ret = redant.view_snaps_from_mount(self.mounts, "snap-0")
        if not ret:
            raise Exception("UnExpected: Unable to list content in activated"
                            " snapshot")
