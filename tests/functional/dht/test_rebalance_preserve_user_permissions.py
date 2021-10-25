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

 You should have received a copy of the GNU General Public License along`
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-131 USA.

 Description:
    Rebalance: permissions check as non root user
"""

# disruptive;dist,dist-rep
import traceback
from tests.d_parent_test import DParentTest


class TestRebalancePreserveUserPermissions(DParentTest):

    def terminate(self):
        """
        Delete the test_user created in the TC
        """
        try:
            if not self.redant.del_user(self.client_list[0], self.user):
                raise Exception("Failed to delete user 'test_user'")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _logged_vol_info(self):
        """Log volume info and status"""
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

    def _check_user_permission(self):
        """
        Verify permissions on MP and file
        """
        stat_mp_dict = self.redant.get_file_stat(self.client_list[0],
                                                 self.mountpoint)
        if stat_mp_dict['error_code'] != 0:
            raise Exception(f"stat on {self.mountpoint} failed")
        if stat_mp_dict['msg']['permission'] != 777:
            raise Exception("Expected 777 but "
                            f"found {stat_mp_dict['msg']['permission']}")

        # check owner and group of random file
        fpath = f"{self.mountpoint}/d1/f.1"
        stat_dict = self.redant.get_file_stat(self.client_list[0], fpath)
        if stat_dict['error_code'] != 0:
            raise Exception(f"stat on {fpath} failed")

        if stat_dict['msg']['user'] != self.user:
            raise Exception(f"Expected {self.user} but "
                            f"found {stat_dict['msg']['user']}")

        if stat_dict['msg']['group'] != self.user:
            raise Exception(f"Expected {self.user} but "
                            f"found {stat_dict['msg']['group']}")

    def _testcase(self, number_of_expands=1):
        """
        Test case:
        1. Create a volume start it and mount on the client.
        2. Set full permission on the mount point.
        3. Add new user to the client.
        4. As the new user create dirs/files.
        5. Compute arequal checksum and check permission on / and subdir.
        6. expand cluster according to number_of_expands and start rebalance.
        7. After rebalance is completed:
        7.1 check arequal checksum
        7.2 verfiy no change in / and sub dir permissions.
        7.3 As the new user create and delete file/dir.
        """
        # Set full permissions on the mount point.
        ret = self.redant.set_file_permissions(self.client_list[0],
                                               self.mountpoint, "-R 777")
        if not ret:
            raise Exception("Failed to set permissions on mountpoint")

        # Create dirs/files as self.test_user
        cmd = (r'su -l %s -c "cd %s;'
               r'for i in {0..9}; do mkdir d\$i; done;'
               r'for i in {0..99}; do let x=\$i%%10;'
               r'dd if=/dev/urandom of=d\$x/f.\$i bs=1024 count=1; done"'
               % (self.user, self.mountpoint))
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # check permission on / and subdir
        self._check_user_permission()

        # get arequal checksum before expand
        arequal_checksum_before = \
            self.redant.collect_mounts_arequal(self.mounts[0])

        self._logged_vol_info()

        # expand the volume
        for i in range(number_of_expands):
            ret = self.redant.expand_volume(self.server_list[0],
                                            self.vol_name, self.server_list,
                                            self.brick_roots)
            if not ret:
                raise Exception(f"Failed to expand iter {i} volume "
                                f"{self.vol_name}")

        self._logged_vol_info()

        # Start Rebalance
        self.redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        ret = self.redant.wait_for_rebalance_to_complete(self.vol_name,
                                                         self.server_list[0])
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # compare arequals checksum before and after rebalance
        arequal_checksum_after = \
            self.redant.collect_mounts_arequal(self.mounts[0])

        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum in NOT equal")

        # permissions check on / and sub dir
        self._check_user_permission()

        # Create/Delete file as self.test_user
        cmd = (f'su -l {self.user} -c "cd {self.mountpoint}; touch file.test;'
               'find . -mindepth 1 -maxdepth 1 -type d | xargs rm -rf"')
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def run_test(self, redant):
        # Add not-root user on client
        self.user = "test_user"
        if not redant.add_user(self.client_list[0], self.user):
            raise Exception("Failed to add user")

        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Case 1: test_rebalance_preserve_user_permissions
        self._testcase()

        # Case 2: test_rebalance_preserve_user_permissions_multi_expands
        self._testcase(2)
