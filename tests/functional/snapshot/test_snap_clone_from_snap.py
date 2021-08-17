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

Test Cases in this module tests the
Creation of clone volume from snapshot.
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;rep,dist,disp,dist-rep,dist-disp


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
        CloneSnapTest contains tests which verifies Clone volume
        created from snapshot

        Steps:

        1. Create a volume
        2. Mount the volume
        3. Perform I/O on mount poit
        4. Create a snapshot
        5. Activate the snapshot created in step 4
        6. Create 10 clones from snapshot created in step 4
        7. Verify Information about the volumes
           along with the original volume.
        8. Validate total number of clone volumes and existing volume
           with volume list
        """

        # write files on all mounts
        counter = 1
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 3, 4, 10,
                                                      mount['client'])
            self.all_mounts_procs.append(proc)
            counter += 10

        # Wait till IO finishes.
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed.")

        # Creating snapshot:
        snap_name = f"{self.vol_name}-snap"
        redant.snap_create(self.vol_name, snap_name, self.server_list[0])

        # Activating snapshot
        redant.snap_activate(snap_name, self.server_list[0])

        # Creating and starting a Clone of snapshot:
        for count in range(1, 11):
            clone_name = f"{self.vol_name}-clone{count}"
            redant.snap_clone(snap_name, clone_name, self.server_list[0])

        # Start clone volumes
        for count in range(1, 11):
            clone_name = f"{self.vol_name}-clone{count}"
            redant.volume_start(clone_name, self.server_list[0])

        # Validate Volume Started
        for count in range(1, 11):
            clone_name = f"{self.vol_name}-clone{count}"
            if not redant.is_volume_started(clone_name, self.server_list[1]):
                raise Exception(f"{clone_name} is not started.")

        # validate with list information
        # with 10 clone volume and 1 existing volume
        ret = redant.get_volume_list(self.server_list[0])
        if len(ret) != 11:
            raise Exception(f"Expected 11 volumes. Got {ret}")
