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
    Test lookup directory with subvol down
"""

# disruptive;dist,dist-rep,dist-disp
# TODO: NFS,Samba
from common.ops.gluster_ops.constants import (FILETYPE_DIRS,
                                              TEST_LAYOUT_IS_COMPLETE)
from time import sleep
from tests.d_parent_test import DParentTest


class TestLookupDir(DParentTest):

    def _mkdir_post_hashdown(self, subvols):
        '''
        case -1:
        - bring down a subvol
        - create a directory so that it does not hash to down subvol
        - make sure stat is successful on the dir
        '''
        # Find a non hashed subvolume(or brick)
        nonhashed = self.redant.find_nonhashed_subvol(subvols, "", "parent")
        if nonhashed is None:
            self.redant.logger.error('Error in finding nonhashed subvol '
                                     'for parent')
            return False
        nonhashed_subvol, count = nonhashed

        # bring nonhashed_subbvol offline
        ret = self.redant.bring_bricks_offline(self.vol_name, subvols[count])
        if not ret:
            self.redant.logger.error('Error in bringing down subvolume'
                                     f'{subvols[count]}')
            return False

        # create parent dir
        self.redant.create_dir(self.mountpoint, "parent", self.client_list[0])

        # this confirms both layout and stat of the directory
        ret = (self.redant.validate_files_in_dir(
               self.client_list[0], f"{self.mountpoint}/parent",
               test_type=TEST_LAYOUT_IS_COMPLETE, file_type=FILETYPE_DIRS))
        if not ret:
            self.redant.logger.error("Layout is not complete")
            return False

        # bring up the subvol
        ret = self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                              subvols[count])
        if not ret:
            self.redant.logger.error("Error in bringing back subvol online")
            return False

        # Sleep to allow volume to be mounted successfully after brick is up
        sleep(5)

        # delete parent_dir
        ret = self.redant.rmdir(f"{self.mountpoint}/parent",
                                self.client_list[0])
        if not ret:
            self.redant.logger.error('rmdir failed')
            return False

        return True

    def _mkdir_before_hashdown(self, subvols):
        '''
        case -2:
            - create directory
            - bring down hashed subvol
            - make sure stat is successful on the dir
        '''
        # create parent dir
        self.redant.create_dir(self.mountpoint, "parent", self.client_list[0])

        # find hashed subvol
        hashed = self.redant.find_hashed_subvol(subvols, "", "parent")
        if not hashed:
            self.redant.logger.error('Error in finding hash value')
            return False

        hashed_subvol, count = hashed

        # bring hashed_subvol offline
        ret = self.redant.bring_bricks_offline(self.vol_name, subvols[count])
        if not ret:
            self.redant.logger.error('Error in bringing down subvolume'
                                     f'{subvols[count]}')
            return False

        # this confirms both layout and stat of the directory
        ret = (self.redant.validate_files_in_dir(
               self.client_list[0], f"{self.mountpoint}/parent",
               test_type=TEST_LAYOUT_IS_COMPLETE, file_type=FILETYPE_DIRS))
        if not ret:
            self.redant.logger.error("Layout is not complete")
            return False

        # bring up the subvol
        ret = self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                              subvols[count])
        if not ret:
            self.redant.logger.error("Error in bringing back subvol online")
            return False

        # Sleep to allow volume to be mounted successfully after brick is up
        sleep(5)

        # delete parent_dir
        ret = self.redant.rmdir(f"{self.mountpoint}/parent",
                                self.client_list[0])
        if not ret:
            self.redant.logger.error('rmdir failed')
            return False

        return True

    def _mkdir_nonhashed_down(self, subvols):
        '''
        case -3:
            - create dir
            - bringdown a non-hashed subvol
            - make sure stat is successful on the dir
        '''
        # create parent dir
        self.redant.create_dir(self.mountpoint, "parent", self.client_list[0])

        # Find a non hashed subvolume(or brick)
        nonhashed = self.redant.find_nonhashed_subvol(subvols, "", "parent")
        if nonhashed is None:
            self.redant.logger.error('Error in finding nonhashed subvol '
                                     'for parent')
            return False
        nonhashed_subvol, count = nonhashed

        # bring nonhashed_subbvol offline
        ret = self.redant.bring_bricks_offline(self.vol_name, subvols[count])
        if not ret:
            self.redant.logger.error('Error in bringing down subvolume'
                                     f'{subvols[count]}')
            return False

        # this confirms both layout and stat of the directory
        ret = (self.redant.validate_files_in_dir(
               self.client_list[0], f"{self.mountpoint}/parent",
               test_type=TEST_LAYOUT_IS_COMPLETE, file_type=FILETYPE_DIRS))
        if not ret:
            self.redant.logger.error("Layout is not complete")
            return False

        # bring up the subvol
        ret = self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                              subvols[count])
        if not ret:
            self.redant.logger.error("Error in bringing back subvol online")
            return False

        # Sleep to allow volume to be mounted successfully after brick is up
        sleep(5)

        # delete parent_dir
        ret = self.redant.rmdir(f"{self.mountpoint}/parent",
                                self.client_list[0])
        if not ret:
            self.redant.logger.error('rmdir failed')
            return False

        return True

    def run_test(self, redant):
        """
        Steps:
        - Create a volume and start it
        - Mount it on client
        - Get the volume subvols
        - Run mkdir_post_hashdwon case
        - Run mkdir_before_hashdown case
        - Run mkdir_nonhashed_down case
        """
        # calculate hash for name "parent"
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])

        # This populates one brick from one subvolume
        secondary_bricks = []
        for subvol in subvols:
            secondary_bricks.append(subvol[0])

        brickpathlist = []
        for item in secondary_bricks:
            brickpathlist.append(item)

        """
        case -1:
            - bring down a subvol
            - create a directory so that it does not hash to down subvol
            - make sure stat is successful on the dir
        """
        ret = self._mkdir_post_hashdown(subvols)
        if not ret:
            raise Exception('mkdir_post_hashdown failed')

        """
        case -2:
            - create directory
            - bring down hashed subvol
            - make sure stat is successful on the dir
        """
        ret = self._mkdir_before_hashdown(subvols)
        if not ret:
            raise Exception('mkdir_before_hashdown failed')

        """
        case -3:
            - create dir
            - bringdown unhashed subvol
            - make sure stat is successful on the dir
        """
        ret = self._mkdir_nonhashed_down(subvols)
        if not ret:
            raise Exception('mkdir_nonhashed_down failed')
