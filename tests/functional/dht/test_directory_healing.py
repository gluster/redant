"""
 Copyright (C) 2018-2020 Red Hat, Inc. <http://www.redhat.com>

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
    Test cases in this module tests directory healing
"""

# disruptive;dist-rep,dist-disp,dist-arb
# TODO: NFS
from copyy import deepcopy
from tests.d_parent_test import DParentTest


class TestDirHeal(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Skip for upstream installation
        self.redant.check_gluster_installation(self.server_list, "downstream")

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def run_test(self, redant):
        """
        - Create and start a volume
        - Mount it on a client
        - Bring down a subvol
        - Create a directory so that it does not hash to down subvol
        - Bring up the subvol
        - Check if directory is healed
        """

        # directory that needs to be created
        parent_dir = f"{self.mountpoint}/parent"
        target_dir = f"{self.mountpoint}/parent/child"

        # create parent dir
        redant.create_dir(self.mountpoint, "parent", self.client_list[0])

        # find non-hashed subvol for child
        hashed, non_hashed = [], []
        hash_num = redant.calculate_hash(self.server_list[0], "child")
        bricklist = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not bricklist:
            raise Exception("Failed to get the brick list")

        for brick in bricklist:
            ret = redant.check_hashrange(f"{brick}/parent")
            if not ret:
                raise Exception("Failed to get the hash range")

            hash_range_low = ret[0]
            hash_range_high = ret[1]
            if hash_range_low <= hash_num <= hash_range_high:
                hashed.append(brick)

        non_hashed = [brick for brick in bricklist if brick not in hashed]

        # bring non_hashed offline
        ret = redant.bring_bricks_offline(self.vol_name, non_hashed)
        if not ret:
            raise Exception(f'Error in bringing down brick {brick}')

        # create child directory
        redant.create_dir(self.mountpoint, "parent/child",
                          self.client_list[0])

        # Check that the dir is not created on the down brick
        for brick in non_hashed:
            non_hashed_host, dir_path = brick.split(":")
            brickpath = f"{dir_path}/parent/child"
            ret = redant.execute_abstract_op_node(f"stat {brickpath}",
                                                  non_hashed_host, False)
            if ret['error_code'] == 0:
                raise Exception(f"Expected {brickpath} to be not present "
                                f"on {non_hashed_host}")

        # bring up the subvol
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         non_hashed)
        if not ret:
            raise Exception("Error in bringing back subvol online")

        redant.execute_abstract_op_node(f"ls {target_dir}",
                                        self.client_list[0])

        # check if the directory is created on non_hashed
        for brick in non_hashed:
            non_hashed_host, dir_path = brick.split(":")
            absolutedirpath = f"{dir_path}/parent/child"
            ret = redant.get_file_stat(non_hashed_host, absolutedirpath)
            if ret['error_code'] != 0:
                raise Exception("Unexpected: Stat of path failed")

        # check if directory is healed => i.e. layout is zeroed out
        for brick in non_hashed:
            brick_path = f"{brick}/parent/child"
            ret = redant.check_hashrange(brick_path)
            if not ret:
                raise Exception("Failed to check hash range")

            hash_range_low = ret[0]
            hash_range_high = ret[1]
            if hash_range_low and hash_range_high:
                self.logger.error("Directory is not healed")
