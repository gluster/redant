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
    Test cases in this module tests mkdir operation with subvol down
"""

# disruptive;dist,dist-rep,dist-disp
# TODO: NFS
from time import sleep
from tests.d_parent_test import DParentTest


class TestMkdirHashdown(DParentTest):

    def run_test(self, redant):
        """
        Steps:
        - Create and start a volume
        - Mount it on a client
        - Bring down a subvol
        - Create a directory so that it hashes the down subvol
        - Make sure mkdir does not succeed
        """
        # directory that needs to be created
        parent_dir = f"{self.mountpoint}/parent"
        child_dir = f"{self.mountpoint}/parent/child"

        # get hashed subvol for name "parent"
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols")

        hashed_subvol = redant.find_hashed_subvol(subvols, "", "parent")
        if not hashed_subvol:
            raise Exception("Could not find hashed subvol")

        hashed, count = hashed_subvol

        # bring target_brick offline
        redant.bring_bricks_offline(self.vol_name, subvols[count])
        ret = redant.are_bricks_offline(self.vol_name, subvols[count],
                                        self.server_list[0])
        if not ret:
            raise Exception('Error in bringing down subvolume'
                            f' {subvols[count]}')

        # create parent dir
        ret = redant.create_dir(self.mountpoint, "parent",
                                self.client_list[0], excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected:mkdir of 'parent' should have failed")

        # check that parent_dir does not exist on any bricks and client
        bricklist = redant.create_brickpathlist(subvols, "parent")
        for brickdir in bricklist:
            host, bpath = brickdir.split(":")
            if redant.path_exists(host, bpath):
                raise Exception("Unexpected: dir 'parent' should not exist on"
                                " servers")

        for client in self.client_list:
            if redant.path_exists(client, parent_dir):
                raise Exception("Unexpected: dir 'parent' should not exist on"
                                " clients")

        # Bring up the subvols and create parent directory
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   subvols[count])
        ret = redant.are_bricks_online(self.vol_name, subvols[count],
                                       self.server_list[0])
        if not ret:
            raise Exception("Error in bringing back subvol online:",
                            f" {subvols[count]}")

        # Adding sleep, as sometimes the mountpoint it not yet connected
        # after the bricks are online
        sleep(5)

        redant.create_dir(self.mountpoint, "parent", self.client_list[0])

        # get hash subvol for name "child"
        hashed_subvol = redant.find_hashed_subvol(subvols, "parent", "child")
        if not hashed_subvol:
            raise Exception("Could not find hashed subvol")
        hashed, count = hashed_subvol

        # bring target_brick offline
        redant.bring_bricks_offline(self.vol_name, subvols[count])
        ret = redant.are_bricks_offline(self.vol_name, subvols[count],
                                        self.server_list[0])
        if not ret:
            raise Exception('Error in bringing down subvolume'
                            f' {subvols[count]}')

        # create child dir
        ret = redant.create_dir(f"{self.mountpoint}/parent", "child",
                                self.client_list[0], excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected:mkdir of 'child' should have failed")

        # check if child_dir exists on any bricks
        bricklist = redant.create_brickpathlist(subvols, "parent/child")
        for brickdir in bricklist:
            host, bpath = brickdir.split(":")
            if redant.path_exists(host, bpath):
                raise Exception("Unexpected: dir 'child' should not exist on"
                                " servers")

        for client in self.client_list:
            if redant.path_exists(client, child_dir):
                raise Exception("Unexpected: dir 'child' should not exist on"
                                " clients")
