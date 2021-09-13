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
    Test Cases in this module tests the creation of snapshot and USS feature.
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
from tests.d_parent_test import DParentTest


class TestSnapshotUssSnap(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. Create a volume and mount it.
        2. Perform I/O on mounts
        3. create a .snaps directory and create some files
        4. Create Multiple snapshots of volume
        5. Check info of volume
        6. Enable USS for volume
        7. Validate files created under .snaps
        8. Disable USS
        9. Again Validate the files created under .snaps directory
        """
        # write files on all mounts
        all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for mount_obj in self.mounts:
            proc = redant.create_files('1k', mount_obj['mountpath'],
                                       mount_obj['client'], 10, 'file')
            all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # starting I/O
        all_mounts_procs = []
        for mount_obj in self.mounts:
            self.mpoint = f"{mount_obj['mountpath']}/.snaps"
            ret = redant.path_exists(mount_obj['client'], self.mpoint)
            if not ret:
                redant.execute_abstract_op_node(f"mkdir -p {self.mpoint}",
                                                mount_obj['client'])
                break
            else:
                # Validate USS running
                ret = redant.is_uss_enabled(self.vol_name, self.server_list[0])
                if not ret:
                    break
                else:
                    redant.disable_uss(self.vol_name, self.server_list[0])
                    redant.execute_abstract_op_node(f"mkdir -p {self.mpoint}",
                                                    mount_obj['client'])
            proc = redant.create_files('1k', mount_obj['mountpath'],
                                       mount_obj['client'], 10, 'foo')
            all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # List files under created .snaps directory
        before_uss_enable = []
        for mount_obj in self.mounts:
            ret = redant.uss_list_snaps(mount_obj['client'],
                                        mount_obj['mountpath'])
            file_list = "".join(ret['msg']).strip().split('\n')
            # deleting the mount path from list
            del file_list[0]
            for file in file_list:
                before_uss_enable.append(file)

        # Create Multiple snapshots for volume
        self.snaps_list = []
        for snap_count in range(1, 5):
            self.snap = f"snap{snap_count}"
            redant.snap_create(self.vol_name, self.snap, self.server_list[0])
            self.snaps_list.append(self.snap)

        # Activate the snapshots
        for snap in self.snaps_list:
            redant.snap_activate(snap, self.server_list[0])

        # snapshot list
        ret = redant.snap_list(self.server_list[0])
        if int(ret['msg']['snapList']['count']) != 4:
            raise Exception("Failed to list all snaps")

        # Enable USS
        redant.enable_uss(self.vol_name, self.server_list[0])

        # Validate USS running
        ret = redant.is_uss_enabled(self.vol_name, self.server_list[0])
        if not ret:
            raise Exception("USS is not enabled")

        # Validate snapshots under .snaps folder
        ret = redant.view_snaps_from_mount(self.mounts, self.snaps_list)
        if not ret:
            raise Exception("Failed to view snaps on mountpoints")

        # Disable USS running
        redant.disable_uss(self.vol_name, self.server_list[0])

        # check snapshots are listed
        after_uss_disable = []
        for mount_obj in self.mounts:
            ret = redant.uss_list_snaps(mount_obj['client'],
                                        mount_obj['mountpath'])
            file_list = "".join(ret['msg']).strip().split('\n')
            # deleting the mount path from list
            del file_list[0]
            for file in file_list:
                after_uss_disable.append(file)

        # Validate after disabling USS, all files should be same
        for file in before_uss_enable:
            if file not in after_uss_disable:
                raise Exception("Files are not same under .snaps")
