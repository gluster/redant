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
    TC to verify custom xattr when subvol up/down
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
from time import sleep
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestCustomXattrHealingForDir(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Skip for upstream installation for dist-disp vol
        if self.volume_type == "dist-disp":
            self.redant.check_gluster_installation(self.server_list,
                                                   "downstream")

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

    def _set_xattr_value(self, fattr_value="bar2"):
        """Set the xattr 'user.foo' as per the value on dir1"""
        # Set the xattr on the dir1
        ret = self.redant.set_fattr(f'{self.mountpoint}/dir1', 'user.foo',
                                    self.client_list[0], fattr_value)
        if ret['error_code'] != 0:
            raise Exception("Failed to set the xattr on dir1")

    def _check_xattr_value_on_mnt(self, expected_value=None):
        """Check if the expected value for 'user.foo'
        is present for dir1 on mountpoint"""
        ret = self.redant.get_fattr(f'{self.mountpoint}/dir1', 'user.foo',
                                    self.client_list[0], encode="text",
                                    excep=False)
        if ret['error_code'] != 0:
            if expected_value is None and "No such attribute" \
               not in ret['error_msg']:
                raise Exception("Xattr is not NONE as expected")
        else:
            val = ret['msg'][1].split('=')[1].strip()
            if val[1:-1] != expected_value:
                raise Exception("Failed to get the xattr"
                                f" on:{self.client_list[0]}")

    def _check_xattr_value_on_bricks(self, online_bricks,
                                     expected_value=None):
        """Check if the expected value for 'user.foo'is present
        for dir1 on backend bricks"""
        for brick in online_bricks:
            host, brick_path = brick.split(':')
            ret = self.redant.get_fattr(f'{brick_path}/dir1', 'user.foo',
                                        host, encode="text", excep=False)
            if ret['error_code'] != 0:
                if expected_value is None and "No such attribute" \
                   not in ret['error_msg']:
                    raise Exception("Xattr is not NONE as expected")
            else:
                val = ret['msg'][1].split('=')[1].strip()
                if val[1:-1] != expected_value:
                    raise Exception("Failed to get the xattr"
                                    f" on:{self.client_list[0]}")

    def _perform_lookup(self):
        """Perform lookup on mountpoint"""
        cmd = f"ls -lR {self.mountpoint}/dir1"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])
        sleep(5)

    def _create_xattr_check_self_heal(self):
        """Create custom xattr and check if its healed"""
        # Set the xattr on the dir1
        self._set_xattr_value(fattr_value="bar2")

        # Get online brick list
        online_bricks = (self.redant.get_online_bricks_list(self.vol_name,
                         self.server_list[0]))
        if not online_bricks:
            raise Exception("Failed to get online bricks")

        # Check if the custom xattr is being displayed on the
        # mount-point for dir1
        self._check_xattr_value_on_mnt(expected_value="bar2")

        # Check if the xattr is being displayed on the online-bricks
        # for dir1
        self._check_xattr_value_on_bricks(online_bricks, expected_value="bar2")

        # Modify custom xattr value on dir1
        self._set_xattr_value(fattr_value="ABC")

        # Lookup on moint-point to refresh the value of xattr
        self._perform_lookup()

        # Check if the modified custom xattr is being displayed
        # on the mount-point for dir1
        self._check_xattr_value_on_mnt(expected_value="ABC")

        # Check if the modified custom xattr is being
        # displayed on the bricks for dir1
        self._check_xattr_value_on_bricks(online_bricks, expected_value="ABC")

        # Remove the custom xattr from the mount point for dir1
        self.redant.delete_fattr(f'{self.mountpoint}/dir1', 'user.foo',
                                 self.client_list[0])

        # Lookup on moint-point to refresh the value of xattr
        self._perform_lookup()

        # Check that the custom xattr is not displayed on the
        # for dir1 on mountpoint
        self._check_xattr_value_on_mnt()

        # Check that the custom xattr is not displayed on the
        # for dir1 on the backend bricks
        self._check_xattr_value_on_bricks(online_bricks)

        # Check if the trusted.glusterfs.pathinfo is displayed
        # for dir1 on mointpoint
        self.redant.get_fattr(f'{self.mountpoint}/dir1',
                              'trusted.glusterfs.pathinfo',
                              self.client_list[0])

        # Set the xattr on the dir1
        self._set_xattr_value(fattr_value="star1")

        # Bring back the bricks online
        self.redant.volume_start(self.vol_name, self.server_list[0],
                                 force=True)

        # Execute lookup on the mointpoint
        self._perform_lookup()

        # Get online brick list
        online_bricks = (self.redant.get_online_bricks_list(self.vol_name,
                         self.server_list[0]))
        if not online_bricks:
            raise Exception("Failed to get online bricks")

        # Check if the custom xattr is being displayed
        # on the mount-point for dir1
        self._check_xattr_value_on_mnt(expected_value="star1")

        # Check if the custom xattr is displayed on all the bricks
        self._check_xattr_value_on_bricks(online_bricks,
                                          expected_value="star1")

    def run_test(self, redant):
        """
        Case 1: test_custom_xattr_with_subvol_down_dir_exists
        Steps:
        1) Create directories from mount point.
        2) Bring one or more(not all) dht sub-volume(s) down by killing
           processes on that server
        3) Create a custom xattr for dir hashed to down sub-volume and also for
           another dir not hashing to down sub-volumes
           # setfattr -n user.foo -v bar2 <dir>
        4) Verify that custom xattr for directory is displayed on mount point
           and bricks for both directories
           # getfattr -n user.foo <dir>
           # getfattr -n user.foo <brick_path>/<dir>
        5) Modify custom xattr value and verify that custom xattr for directory
           is displayed on mount point and all up bricks
           # setfattr -n user.foo -v ABC <dir>
        6) Verify that custom xattr is not displayed once you remove it on
           mount point and all up bricks
        7) Verify that mount point shows pathinfo xattr for dir hashed to down
           sub-volume and also for dir not hashed to down sub-volumes
           # getfattr -n trusted.glusterfs.pathinfo <dir>
        8) Again create a custom xattr for dir not hashing to down sub-volumes
           # setfattr -n user.foo -v star1 <dir>
        9) Bring up the sub-volumes
        10) Execute lookup on parent directory of both <dir> from mount point
        11) Verify Custom extended attributes for dir1 on all bricks
        """
        # Create dir1 on client0
        redant.create_dir(self.mountpoint, "dir1", self.client_list[0])

        # Get subvol list
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")

        # Finding a dir name such that it hashes to a different subvol
        newhash = redant.find_new_hashed(subvols, "", "dir1")
        if not newhash:
            raise Exception("Failed to get new hash")

        new_name = str(newhash[0])
        new_subvol_count = newhash[2]

        # Create a dir with the new name
        redant.create_dir(self.mountpoint, new_name, self.client_list[0])

        # Kill the brick/subvol to which the new dir hashes
        ret = redant.bring_bricks_offline(self.vol_name,
                                          subvols[new_subvol_count])
        if not ret:
            raise Exception('Error in bringing down subvolume')

        # Set the xattr on dir hashing to down subvol
        ret = redant.set_fattr(f'{self.mountpoint}/{new_name}', 'user.foo',
                               self.client_list[0], 'bar2')
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Successfully set the xattr on dir1")

        # Check if the trusted.glusterfs.pathinfo is displayed
        # for dir hashing to down subvol on mointpoint
        redant.get_fattr(f'{self.mountpoint}/{new_name}',
                         'trusted.glusterfs.pathinfo',
                         self.client_list[0])

        # Calling the local function
        self._create_xattr_check_self_heal()

        # Clear the mountpoint, before moving to next case
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_custom_xattr_with_subvol_down_dir_doesnt_exists
        """
        Steps:
        1) Bring one or more(not all) dht sub-volume(s) down by killing
           processes on that server
        2) Create a directory from mount point such that it
           hashes to up subvol.
        3) Create a custom xattr for dir
           # setfattr -n user.foo -v bar2 <dir>
        4) Verify that custom xattr for directory is displayed on mount point
           and bricks for directory
           # getfattr -n user.foo <dir>
           # getfattr -n user.foo <brick_path>/<dir>
        5) Modify custom xattr value and verify that custom xattr for directory
           is displayed on mount point and all up bricks
           # setfattr -n user.foo -v ABC <dir>
        6) Verify that custom xattr is not displayed once you remove it on
           mount point and all up bricks
        7) Verify that mount point shows pathinfo xattr for dir
        8) Again create a custom xattr for dir
           # setfattr -n user.foo -v star1 <dir>
        9) Bring up the sub-volumes
        10) Execute lookup on parent directory of both <dir> from mount point
        11) Verify Custom extended attributes for dir1 on all bricks
        """
        # Get subvol list
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")

        # Find out the hashed subvol for dir1
        srchashed = redant.find_hashed_subvol(subvols, "", "dir1")
        if not srchashed:
            raise Exception("Could not find srchashed")
        subvol_count = srchashed[1]

        # Remove the hashed_subvol from subvol list
        subvols.remove(subvols[subvol_count])

        # Bring down a dht subvol
        ret = redant.bring_bricks_offline(self.vol_name, subvols[0])
        if not ret:
            raise Exception('Error in bringing down subvolume')

        # Create the dir1
        redant.create_dir(self.mountpoint, "dir1", self.client_list[0])

        # Calling the local function
        self._create_xattr_check_self_heal()
