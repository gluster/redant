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

Test Description:
    Verify Eager lock reduces the number of locks
    being taken when writing to the file continuosly
"""
# nonDisruptive;disp,dist-disp
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):
    def _check_dirty_xattr(self, filename):
        """Get trusted.ec.dirty xattr value to validate eagerlock behavior
        """
        # Collect ec.dirty xattr value from each brick
        result = []
        bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        if not bricks_list:
            raise Exception("Failed to get the brick list")

        for brick in bricks_list:
            host, brickpath = brick.split(':')
            brickpath = f"{brickpath}/{filename}"
            ret = self.redant.get_extended_attributes_info(host, brickpath)
            if not ret:
                continue
            ret = ret[brickpath]['trusted.ec.dirty']
            result.append(ret)

        # Check if xattr values are same across all bricks
        if result.count(result[0]) == len(result):
            return ret
        self.redant.logger.error("trusted.ec.dirty value is not consistent "
                                 "across the "
                                 f"disperse set {result}")
        return None

    def _file_create_and_profile_info(self, status):
        """Create a file and check the volume profile for inode lock count."""
        # Creating file
        filename = 'f1_EagerLock_' + status
        cmd = (f"dd if=/dev/urandom of={self.mountpoint}/{filename} "
               "bs=100M count=10")
        self.redant.execute_abstract_op_node(cmd, self.server_list[0])

        # Getting and checking output of profile info.
        cmd = (f"gluster v profile {self.vol_name} info | grep -i INODELK"
               " | awk '{print$8}'")
        ret = self.redant.execute_abstract_op_node(cmd, self.server_list[0])
        if ret['msg'] is None:
            raise Exception("Failed to grep INODELK count from profile")

        return filename

    def run_test(self, redant):
        """
        Test Steps:
        1) Create an ecvolume and mount it
        2) Set the eagerlock option
        3) Create a 1GB file
        4) View the profile of the volume for INODELK count must be about
           2-10 locks for each brick.
        5) check backend bricks for trusted.ec.dirty xattr must be non-zero
        6) Disable the eagerlock option
        7) Repeat steps 3-5 and now dirty xattr must be zero and
           INODELK count in range of 100-5k.
        """

        # Enable EagerLock
        redant.set_volume_options(self.vol_name,
                                  {'disperse.eager-lock': 'on',
                                   'disperse.eager-lock-timeout': '30'},
                                  self.server_list[0], True)

        # Start profile on volume.
        redant.profile_start(self.vol_name, self.server_list[0])

        # Test behavior with EagerLock on
        filename = self._file_create_and_profile_info("on")
        if filename is None:
            raise Exception("Failed to get filename")

        # Test dirty bit with EagerLock on
        ret = self._check_dirty_xattr(filename)
        if ret != '0x00000000000000010000000000000001':
            raise Exception("Unexpected dirty xattr value is set: "
                            f"{ret} on {filename}")

        # Disable EagerLock
        redant.set_volume_options(self.vol_name,
                                  {'disperse.eager-lock': 'off'},
                                  self.server_list[0])

        # Test behavior with EagerLock off
        filename = self._file_create_and_profile_info("off")
        if filename is None:
            raise Exception("Failed to get filename")

        # Test dirty bit with EagerLock off
        ret = self._check_dirty_xattr(filename)
        if ret != '0x00000000000000000000000000000000':
            raise Exception("Unexpected dirty xattr value is set: "
                            f"{ret} on {filename}")

        # Stop profile on volume.
        redant.profile_stop(self.vol_name, self.server_list[0])
