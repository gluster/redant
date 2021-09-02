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
    Test Cases in this module tests the creation of clone from snapshot
    of volume.
"""

# disruptive;dist-rep
from tests.d_parent_test import DParentTest


class TestSnapshotSelfheal(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        1. create a volume
        2. mount volume
        3. create snapshot of that volume
        4. Activate snapshot
        5. Clone snapshot and Mount
        6. Perform I/O
        7. Bring Down Few bricks from volume without
           affecting the volume or cluster.
        8. Perform I/O
        9. Bring back down bricks to online
        10. Validate heal is complete with areequal
        """
        self.snap = "snap1"
        self.clone = "clone1"
        self.mount1 = "/mnt/clone1"

        # Creating snapshot:
        redant.snap_create(self.vol_name, self.snap, self.server_list[0])

        # Activating snapshot
        redant.snap_activate(self.snap, self.server_list[0])

        # snapshot list
        redant.snap_list(self.server_list[0])

        # Creating a Clone volume from snapshot:
        redant.snap_clone(self.clone, self.snap, self.server_list[0])

        #  start clone volumes
        redant.volume_start(self.clone, self.server_list[0])

        # Mounting a clone volume
        redant.execute_abstract_op_node(f"mkdir -p {self.mount1}",
                                        self.client_list[0])
        redant.volume_mount(self.server_list[0], self.clone, self.mount1,
                            self.client_list[0])

        # Checking cloned volume mounted or not
        if not redant.is_mounted(self.clone, self.mount1, self.client_list[0],
                                 self.server_list[0]):
            raise Exception("Cloned Volume not mounted on mount point: "
                            f"{self.mount1}")

        # write files on all mounts
        proc = redant.create_files('1k', self.mount1, self.client_list[0], 10,
                                   'file')

        # Validate IO
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mount1
        }
        if not redant.validate_io_procs(proc, self.mounts):
            raise Exception("IO failed on some of the clients")

        # get the bricks from the volume
        bricks_list = redant.get_all_bricks(self.clone, self.server_list[0])
        if not bricks_list:
            raise Exception("Failed to get the brick list")

        # Select bricks to bring offline
        offline_bricks = (redant.select_volume_bricks_to_bring_offline(
                          self.vol_name, self.server_list[0]))

        if not redant.bring_bricks_offline(self.clone, offline_bricks):
            raise Exception("Failed to bring the bricks offline")

        # Offline Bricks list
        offline_bricks_list = (redant.get_offline_bricks_list(self.clone,
                               self.server_list[0]))
        if not offline_bricks_list:
            raise Exception("Failed to get offline bricklist"
                            f"for volume {self.clone}")

        for bricks in offline_bricks_list:
            if bricks not in offline_bricks:
                raise Exception("Failed to validate offline bricks list")

        # Online Bricks list
        online_bricks = redant.get_online_bricks_list(self.clone,
                                                      self.server_list[0])
        if not online_bricks:
            raise Exception("Failed to get online bricklist"
                            f"for volume {self.clone}")

        # write files mountpoint
        proc = redant.create_files('1k', self.mount1, self.client_list[0], 10)

        # Validate IO
        if not redant.validate_io_procs(proc, self.mounts):
            raise Exception("IO failed on some of the clients")

        # Bring all bricks online
        redant.bring_bricks_online(self.clone, self.server_list,
                                   offline_bricks)

        # Validate Bricks are online
        if not redant.are_bricks_online(self.clone, bricks_list,
                                        self.server_list[0]):
            raise Exception("Failed to bring all the bricks online")

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.clone,
                self.server_list[0], self.server_list)):
            raise Exception("Few volume processess are offline for the "
                            f"volume: {self.clone}")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.clone,
                self.server_list[0])):
            raise Exception("Few process after volume start are offline for"
                            f" volume: {self.clone}")

        # wait for the heal process to complete
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.clone):
            raise Exception("Heal has not yet completed")

        # Check arequal
        # get the subvolumes
        subvols = redant.get_subvols(self.clone, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols for the volume")
        num_subvols = len(subvols)

        # Get arequals and compare
        for i in range(0, num_subvols):
            # Get arequal for first brick
            arequal = self.redant.collect_bricks_arequal(subvols[i][0])
            first_brick_total = arequal[0][-1].split(':')[-1]

            # Get arequal for every brick and compare with first brick
            arequals = self.redant.collect_bricks_arequal(subvols[i])
            for arequal in arequals:
                brick_total = arequal[-1].split(':')[-1]
                if first_brick_total != brick_total:
                    raise Exception('Arequals for subvol and brick are '
                                    'not equal')
