"""
 Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

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
    TC to test directory entry creation when a subvol is down
"""

# disruptive;dist-arb,dist-rep
from time import sleep
from tests.d_parent_test import DParentTest


class TestAfrDirEntryCreationWithSubvolDown(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        conf_hash['dist_count'] = 3
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

    def _check_file_exists(self, subvol, directory, exists=True):
        """ Validates given directory present on brick path of each subvol """
        for each_brick in subvol:
            node, brick_path = each_brick.split(":")
            path = brick_path + directory
            ret = self.redant.path_exists(node, path)
            if ret != exists:
                raise Exception("Unexpected behaviour on existence "
                                f"check of directory {directory} on brick "
                                f"{each_brick}")

    def _create_file(self, location, file_name):
        """ Creates a file with file_name on the specified location"""
        source_file = f"{location}/{file_name}"
        self.redant.execute_abstract_op_node(f"touch {source_file}",
                                             self.client_list[0])

    def _create_number_of_files_on_the_subvol(self, subvol, directory,
                                              number_of_files, mountpath):
        """Creates number of files specified on the given subvol"""
        name = None
        for _ in range(number_of_files):
            hashed = self.redant.find_specific_hashed(self.subvols, directory,
                                                      subvol, name)
            if hashed is None:
                raise Exception("Couldn't find a subvol to "
                                "create a file.")

            self._create_file(mountpath, hashed[0])
            name = hashed[0]

    def run_test(self, redant):
        """
        1. Create a distributed-replicated(3X3)/distributed-arbiter(3X(2+1))
           and mount it on one client
        2. Kill 3 bricks corresponding to the 1st subvol
        3. Unmount and remount the volume on the same client
        4. Create deep dir from mount point
           mkdir -p dir1/subdir1/deepdir1
        5. Create files under dir1/subdir1/deepdir1; touch <filename>
        6. Now bring all sub-vols up by volume start force
        7. Validate backend bricks for dir creation, the subvol which is
           offline will have no dirs created, whereas other subvols will have
           dirs created from step 4
        8. Trigger heal from client by "#find . | xargs stat"
        9. Verify that the directory entries are created on all back-end bricks
        10. Create new dir (dir2) on location dir1/subdir1/deepdir1
        11. Trigger rebalance and wait for the completion
        12. Check backend bricks for all entries of dirs
        13. Check if files are getting created on the subvol which was offline
        """
        # Bring down first subvol of bricks offline
        self.subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        first_subvol = self.subvols[0]
        redant.bring_bricks_offline(self.vol_name, first_subvol)

        # Check bricks are offline or not
        if not redant.are_bricks_offline(self.vol_name, first_subvol,
                                         self.server_list[0]):
            raise Exception(f"Bricks {first_subvol} are still online")

        # Unmount and remount the volume
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        # At this step, sleep is must otherwise file creation will fail
        sleep(2)

        # Create dir `dir1/subdir1/deepdir1` on mountpont
        directory1 = "dir1/subdir1/deepdir1"
        path = f"{self.mountpoint}/{directory1}"
        redant.create_dir(self.mountpoint, directory1, self.client_list[0])

        # Create files on the 2nd and 3rd subvols which are online
        bricklist = redant.create_brickpathlist(self.subvols, directory1)
        if not bricklist:
            raise Exception("Failed to get brickpath list")

        self._create_number_of_files_on_the_subvol(
            bricklist[1], directory1, 5, mountpath=path)
        self._create_number_of_files_on_the_subvol(
            bricklist[2], directory1, 5, mountpath=path)

        # Bring bricks online using volume start force
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Check all bricks are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("Few process after volume start are offline for "
                            f"volume: {self.vol_name}")

        # Validate Directory is not created on the bricks of the subvol which
        # is offline
        for subvol in self.subvols:
            self._check_file_exists(subvol, f"/{directory1}",
                                    exists=(subvol != first_subvol))

        # Trigger heal from the client
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = redant.get_mounts_stat(self.mounts)
        if not ret:
            raise Exception("Failed to do stat on mountpoint")

        # Validate the directory1 is present on all the bricks
        for subvol in self.subvols:
            self._check_file_exists(subvol, f"/{directory1}", exists=True)

        # Create new dir (dir2) on location dir1/subdir1/deepdir1
        directory2 = f"/{directory1}/dir2"
        path = f"{self.mountpoint}/{directory2}"
        redant.create_dir(self.mountpoint, directory2, self.client_list[0])

        # Trigger rebalance and validate the completion
        redant.rebalance_start(self.vol_name, self.server_list[0])
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0])
        if not ret:
            raise Exception("Rebalance didn't complete on the volume: "
                            f"{self.vol_name}")

        # Validate all dirs are present on all bricks in each subvols
        for subvol in self.subvols:
            for each_dir in (f"/{directory1}", directory2):
                self._check_file_exists(subvol, each_dir, exists=True)

        # Validate if files are getting created on the subvol which was
        # offline
        self._create_number_of_files_on_the_subvol(
            bricklist[0], directory1, 5, mountpath=path)
