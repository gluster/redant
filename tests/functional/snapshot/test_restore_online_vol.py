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
    This test case will validate snap restore on online volume.
    When we try to restore online volume it should fail.
"""

# disruptive;rep,dist,disp,dist-rep,dist-disp
# TODO:nfs,cifs

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")
        except Exception as e:
            tb = traceback.format_exc()
            self.redant.logger.error(e)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1. Create volume
        2. Mount volume
        3. Perform I/O on mounts
        4. Create 1 snapshots snapy1
        5. Validate snap created
        6. Perform some more I/O
        7. Create 1 more snapshot snapy2
        8. Restore volume to snapy1
          -- Restore should fail with message
             "volume needs to be stopped before restore"
        """
        self.io_validation_complete = True
        # Performing step 3 to 7 in loop here
        for i in range(1, 3):
            # Perform I/O
            self.counter = 1
            self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
            self.all_mounts_procs = []
            for mount_obj in self.mounts:
                redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                                   f"{mount_obj['mountpath']}")
                proc = (redant.create_deep_dirs_with_files(
                        mount_obj['mountpath'], self.counter, 2, 2, 2, 2,
                        mount_obj['client']))

                self.counter += 100
                self.all_mounts_procs.append(proc)
            self.io_validation_complete = False

            # Validate IO
            if not redant.validate_io_procs(self.all_mounts_procs,
                                            self.mounts):
                raise Exception("IO failed on client")
            self.io_validation_complete = True

            # Get stat of all the files/dirs created.
            if not redant.get_mounts_stat(self.mounts):
                raise Exception("Stat on mountpoints failed.")

            # Create snapshot
            snapname = f"{self.vol_name}-snap{i}"
            redant.snap_create(self.vol_name, snapname, self.server_list[0])

            # Check for no of snaps using snap_list
            snap_list = redant.get_snap_list(self.server_list[0])
            if len(snap_list) != i:
                raise Exception("Number of snaps not consistent for volume"
                                f" {self.vol_name}")

            # Increase counter for next iteration
            self.counter = 1000

        # Restore volume to snapshot snapy2, it should fail
        i = 2
        snapname = f"{self.vol_name}-snap{i}"
        ret = redant.snap_restore(snapname, self.server_list[0])
        if ret['error_code'] == 0:
            raise Exception("Expected : Failed to restore volume to snap")
