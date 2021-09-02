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
    The purpose of this test is to validate snapshot
    hard and soft max-limt options.
"""

# disruptive;rep,dist-rep,disp,dist,dist-disp
# TODO: NFS,CIFS
from tests.d_parent_test import DParentTest


class TestSnapCreateMax(DParentTest):

    def run_test(self, redant):
        """
        Steps :
        1. Create and start a volume
        2. Mount the volume on a client
        3. Perform some heavy IO
        4. Varify IO
        5. modify max snap limit to default to 10.
        6. modify soft-limit to 50%
        6. Create 5 snapshots
        7. Varify 5 created successfully
        8. Create 6th snapshot -  check for warning
           -- it should not fail.
        9. modify soft-limit to 100%
        10. Create 7th snapshot -  check for warning
           -- it should not show warning.
        11. Reach the snap-max-hard-limit by creating more snapshots
        12. Create 11th snapshot - check for failure
           -- it shoul fail.
        13. varify the no. of snpas it should be 10.
        14. modify max snap limit to 20
        15. create 10 more snaps
        16. varify the no. of snpas it should be 20
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Start IO on all mounts.
        all_mounts_procs = []
        count = 1
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 5, 5, 5,
                                                      mount_obj['client'])
            all_mounts_procs.append(proc)
            count = count + 10

        # Validate IO
        if not redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO failed.")

        # Get stat of all the files/dirs created.
        ret = redant.get_mounts_stat(self.mounts)
        if not ret:
            raise Exception("Stat failed on some of the clients")

        # set config snap-max-hard-limit for 10 snpas
        max_hard_limit = {'snap-max-hard-limit': '10'}
        redant.set_snap_config(max_hard_limit, self.server_list[0],
                               self.vol_name)

        # set config snap-max-soft-limit to 50%
        max_soft_limit = {'snap-max-soft-limit': '50'}
        redant.set_snap_config(max_soft_limit, self.server_list[0])

        # Create 5 snaps
        for i in range(1, 6):
            redant.snap_create(self.vol_name, f"snapy{i}",
                               self.server_list[0])

        # Check for no. of snaps using snap_list it should be 5
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 5:
            raise Exception(f"Expected 5 snapshots. Found {len(snap_list)}"
                            " snapshots")

        # Validate all 5 snap names present in snap_list
        for i in range(1, 6):
            if f"snapy{i}" not in snap_list:
                raise Exception(f"snapy{i} snap not found in {snap_list}")

        # create 6th snapshot
        redant.snap_create(self.vol_name, "snapy6", self.server_list[0])

        # set config snap-max-soft-limit to 100%
        max_soft_limit = {'snap-max-soft-limit': '100'}
        redant.set_snap_config(max_soft_limit, self.server_list[0])

        # create 7th snapshot
        redant.snap_create(self.vol_name, "snapy7", self.server_list[0])

        # Create 3 snaps
        for i in range(8, 11, 1):
            redant.snap_create(self.vol_name, f"snapy{i}",
                               self.server_list[0])

        # Check for no. of snaps using snap_list it should be 10
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 10:
            raise Exception(f"Expected 10 snapshots. Found {len(snap_list)}"
                            " snapshots")

        # Validate all 10 snap names created
        for i in range(1, 11, 1):
            if f"snapy{i}" not in snap_list:
                raise Exception(f"snapy{i} snap not found in {snap_list}")

        # create 11th snapshot
        ret = redant.snap_create(self.vol_name, "snapy11",
                                 self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully created 11th snapshot")

        # Check for no. of snaps using snap_list it should be 10
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 10:
            raise Exception(f"Expected 10 snapshots. Found {len(snap_list)}"
                            " snapshots")

        # modify config snap-max-hard-limit for 20 snpas
        max_hard_limit = {'snap-max-hard-limit': '20'}
        redant.set_snap_config(max_hard_limit, self.server_list[0],
                               self.vol_name)

        # Create 10 snaps
        for i in range(11, 21, 1):
            redant.snap_create(self.vol_name, f"snapy{i}",
                               self.server_list[0])

        # Check for no. of snaps using snap_list it should be 20
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 20:
            raise Exception(f"Expected 10 snapshots. Found {len(snap_list)}"
                            " snapshots")
