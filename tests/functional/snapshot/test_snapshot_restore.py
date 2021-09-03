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
    TC to validate restore of a snapshot.
"""

# disruptive;dist-rep,dist-disp
from tests.d_parent_test import DParentTest


class TestSnapRestore(DParentTest):

    def run_test(self, redant):
        """
        Steps :
        1. Create and start a volume
        2. Mount the volume on a client
        3. Create data on the volume (v1)
        4. Set some volume option
        5. Take snapshot of volume
        6. Create some more data on volume (v2)
        7. Reset volume option
        8. Remove brick/bricks
        9. Stop volume
        10. Restore snapshot
        11. Start and mount volume
        12. Validate data on volume (v1)
        13. Validate volume option
        14. Validate bricks after restore
        15. Create snapshot of restored volume
        16. Cleanup
        """
        # Start IO on all mounts.
        all_mounts_proc = []
        count = 1
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for mount in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      count, 2, 3, 2, 5,
                                                      mount['client'])
            all_mounts_proc.append(proc)
            count += 10

        # Validate IO
        if not redant.validate_io_procs(all_mounts_proc, self.mounts):
            raise Exception("IO failed")

        # Get stat of all the files/dirs created.
        ret = redant.get_mounts_stat(self.mounts)
        if not ret:
            raise Exception("Stat failed on some of the clients")

        # Setting some volume option related to snapshot
        option_before_restore = {"diagnostics.brick-log-level": "WARNING"}
        redant.set_volume_options(self.vol_name, option_before_restore,
                                  self.server_list[0])

        # Get brick list before taking snap_restore
        brick_before_snap_restore = redant.get_all_bricks(self.vol_name,
                                                          self.server_list[0])
        if not brick_before_snap_restore:
            raise Exception("Failed to get brick list")

        # Creating snapshot
        redant.snap_create(self.vol_name, "snap1", self.server_list[0])

        # Again start IO on all mounts.
        all_mounts_proc = []
        count = 1000
        for mount in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      count, 2, 3, 2, 5,
                                                      mount['client'])
            all_mounts_proc.append(proc)
            count += 10

        # Validate IO
        if not redant.validate_io_procs(all_mounts_proc, self.mounts):
            raise Exception("IO failed")

        # Get stat of all the files/dirs created.
        ret = redant.get_mounts_stat(self.mounts)
        if not ret:
            raise Exception("Stat failed on some of the clients")

        # Reset volume to make sure volume options will reset
        redant.volume_reset(self.vol_name, self.server_list[0], force=False)

        # Removing one brick
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   force=True)
        if not ret:
            raise Exception(f"Failed to shrink the volume {self.vol_name}")

        # Restore snapshot
        ret = redant.snap_restore_complete(self.vol_name, "snap1",
                                           self.server_list[0])
        if not ret:
            raise Exception("Failed to restore snap snap1 on the "
                            f"volume {self.vol_name}")

        # Validate volume is up and running
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("Few process after volume start are offline for "
                            f"volume: {self.vol_name}")

        # Get volume options post restore
        option = "diagnostics.brick-log-level"
        option_aftr_restore = redant.get_volume_options(self.vol_name,
                                                        option,
                                                        self.server_list[0])
        if option_aftr_restore != option_before_restore:
            raise Exception("Unexpected: Volume Options are not same after "
                            "snap restore")

        # Get brick list post restore
        bricks_after_snap_restore = redant.get_all_bricks(self.vol_name,
                                                          self.server_list[0])
        if not bricks_after_snap_restore:
            raise Exception("Failed to get the brick list")

        if len(bricks_after_snap_restore) != len(brick_before_snap_restore):
            raise Exception("Unexpected: Bricks count is not same after snap"
                            " restore")

        # Creating snapshot
        redant.snap_create(self.vol_name, "snap2", self.server_list[0])

        # Again start IO on all mounts after restore
        all_mounts_proc = []
        count = 2000
        for mount in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      count, 2, 3, 2, 5,
                                                      mount['client'])
            all_mounts_proc.append(proc)
            count += 10

        # Validate IO
        if not redant.validate_io_procs(all_mounts_proc, self.mounts):
            raise Exception("IO failed")

        # Get stat of all the files/dirs created.
        ret = redant.get_mounts_stat(self.mounts)
        if not ret:
            raise Exception("Stat failed on some of the clients")
