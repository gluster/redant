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

Description : The purpose of this test is to validate snapshot create

"""

import traceback
from tests.d_parent_test import DParentTest


# disruptive;rep,dist,disp,dist-rep,dist-disp


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.validate_io_procs = False

        # Skip test if not RHGS installation
        self.redant.check_gluster_installation(self.server_list, "downstream")

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 self.vol_type_inf[self.volume_type],
                                 self.server_list, self.brick_roots,
                                 force=True)

        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

    def terminate(self):
        try:
            if self.validate_io_procs:
                ret = self.redant.wait_for_io_to_complete(self.all_mounts_proc,
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
        Test for snapshot create
        Steps :
        1. Create and start a volume
        2. Create a snapshot of volume using
           -- gluster snapshot create <snap> <vol-name(s)>
        3. Create snapshot of volume using
           -- gluster snapshot create <snap> <vol-name(s)> [description
              <description with words and quotes>]
        4. Create one more snapshot of volume using
           -- gluster snapshot create <snap3> <vol-name(s)> force
        5. Create one snapshot with option no-timestamp
        6. Mount the volume on a client
        7. Perform some heavy IO
        8. While files and directory creation is in progress,
           create multiple gluster snapshots
        9. Do a snapshot list to see if all the snapshots are present
        10. Do a snapshot info to see all the snapshots information
        11. Verify that the IO is not hindered
        12. Arequal all the bricks in the snap volume
        13. Cleanup
        """
        # Creating snapshot with no option
        snap_name = f"{self.vol_name}-snap1"
        redant.snap_create(self.vol_name, snap_name, self.server_list[0],
                           timestamp=True)

        # Create snapshot of volume using
        # -- gluster snapshot create <snap2> <vol-name(s)> [description
        # <description with words and quotes>]
        desc = 'this is a snap with snap name and description'
        snap_name = f"{self.vol_name}-snap2"
        redant.snap_create(self.vol_name, snap_name, self.server_list[0],
                           description=desc, timestamp=True)

        # Create one more snapshot of volume using no-timestamp option
        snap_name = f"{self.vol_name}-snap3"
        redant.snap_create(self.vol_name, snap_name, self.server_list[0])

        # Create snap with force option.
        snap_name = f"{self.vol_name}-snap4"
        redant.snap_create(self.vol_name, snap_name, self.server_list[0],
                           force=True)

        # Delete all snaps
        redant.snap_delete_all(self.server_list[0])

        # Start IO on all mounts.
        self.all_mounts_proc = []
        counter = 1
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 3, 4, 10,
                                                      mount['client'])
            self.all_mounts_proc.append(proc)
            counter += 10
        self.validate_io_procs = True

        for proc in self.all_mounts_proc:
            if redant.check_async_command_status(proc):
                raise Exception(f"{proc} shouldn't have ended.")

        # Create 5 snaps while IO is in progress
        for i in range(5, 10):
            snap_name = f"{self.vol_name}-snap{i}"
            redant.snap_create(self.vol_name, snap_name, self.server_list[0])

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_proc, self.mounts):
            raise Exception("IO failed.")
        self.validate_io_procs = False

        # Get stat of all the files/dirs created.
        if not redant.get_mounts_stat(self.mounts):
            raise Exception("Stat on mountpoints failed.")

        # Check for no of snaps using snap_list it should be 5 now
        snap_list = redant.get_snap_list(self.server_list[0])
        if len(snap_list) != 5:
            raise Exception("Number of snaps from snap list is not 5. Got"
                            f" {snap_list}")

        # Validate all snaps created during IO
        for i in range(5, 10):
            snap_name = f"{self.vol_name}-snap{i}"
            if snap_name not in snap_list:
                raise Exception(f"{snap_name} not present in {snap_list}")
