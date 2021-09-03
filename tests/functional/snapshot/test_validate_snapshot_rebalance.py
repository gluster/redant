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
    The purpose of this test is to validate snapshot create during rebalance
"""

# disruptive;rep,dist-rep,disp,dist,dist-disp
# TODO: NFS,CIFS
from tests.d_parent_test import DParentTest


class TestSnapCreateRebal(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. Create and start a volume
        2. Mount the volume on client
        3. Perform some heavy IO
        4. Create one snapshot with option no-timestamp
        5. Add bricks to the volume using gluster volume
        6. Start Rebalance using gluster v rebalance <vol-name> start
        7. While rebalance is in progress, create gluster snapshot
           -snapshot creation should fail with message : rebalance is runinng
            on the volume. Please try after sometime
        8. Check for snap name and number to validate snaps created or not
           during rebalance
        9. After rebalance is completed, create snapshots with the same name as
           in Step 7
           -- this operation should be successful
        10. Cleanup
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

        # Create one snapshot of volume using no-timestamp option
        redant.snap_create(self.vol_name, "snapy", self.server_list[0])

        # Check for no of snaps using snap_list it should be 1
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 1:
            raise Exception(f"Expected 1 snapshots. Found {len(snap_list)}"
                            " snapshots")

        # validate snap name
        if "snapy" not in snap_list:
            raise Exception(f"snapy snap not found in {snap_list}")

        # get the bricks for the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if not bricks_list:
            raise Exception("Failed to get brick list")

        # expanding volume
        # Use force for dist-dsip volume, due to fault tolerance limitation
        force = False
        if self.volume_type == "dist-disp":
            force = True

        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots, force)
        if not ret:
            raise Exception("Failed to add bricks to "
                            f"volume {self.vol_name}")

        # Log Volume Info and Status after expanding the volume
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Verify volume's all process are online for 60 sec
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list, 60)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Log Rebalance status
        redant.get_rebalance_status(self.vol_name, self.server_list[0])

        # Create one snapshot of volume during rebalance
        ret = redant.snap_create(self.vol_name, "snapy_rebal",
                                 self.server_list[0], excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception("Unexpected: Successfully created snapshot "
                            "while rebalance is in progress")

        # Check for no of snaps using snap_list it should be 1
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 1:
            raise Exception(f"Expected 1 snapshots. Found {len(snap_list)}"
                            " snapshots")

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0])
        if not ret:
            raise Exception("Rebalance is not yet complete "
                            f"on the volume {self.vol_name}")

        # Create one snapshot of volume post rebalance with same name
        redant.snap_create(self.vol_name, "snapy_rebal", self.server_list[0])

        # Check for no of snaps using snap_list it should be 2
        snap_list = redant.get_snap_list(self.server_list[0], self.vol_name)
        if len(snap_list) != 2:
            raise Exception(f"Expected 2 snapshots. Found {len(snap_list)}"
                            " snapshots")

        # validate snap name
        if "snapy_rebal" not in snap_list:
            raise Exception(f"snapy_rebal snap not found in {snap_list}")
