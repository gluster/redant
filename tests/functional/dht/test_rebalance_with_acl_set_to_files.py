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
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# disruptive;dist-rep,dist-arb,dist,rep,arb,dist-disp,disp

import traceback
from tests.d_parent_test import DParentTest


class TestRebalanceWithAclSetToFiles(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0],
                                 option='acl')

    def terminate(self):
        """
        Delete the users created in the TC
        """
        try:
            self.redant.del_user(self.client_list[0], "joker")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _check_acl_set_to_files(self):
        """Check acl values set to files"""
        for number in range(1, 11):
            ret = self.redant.get_acl(self.client_list[0], self.mountpoint,
                                      f'file{number}')
            if 'user:joker:rwx\n' not in ret['msg']:
                raise Exception("Rule not present in getfacl output")

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it to a client.
        2. Create 10 files on the mount point and set acls on the files.
        3. Check the acl value and collect arequal-checksum.
        4. Add bricks to the volume and start rebalance.
        5. Check the value of acl(it should be same as step 3),
           collect and compare arequal-checksum with the one collected
           in step 3
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        # Create user
        if not redant.add_user(self.client_list[0], 'joker'):
            raise Exception("Failed to create user joker")

        # Create 10 files on the mount point.
        cmd = (f"cd {self.mountpoint}; for i in `seq 1 10`;do touch file$i;"
               "done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        for number in range(1, 11):
            if not (redant.set_acl(self.client_list[0], 'u:joker:rwx',
                    f'{self.mountpoint}/file{number}')):
                raise Exception("Failed to set acl on files")

        # Collect arequal on mount point and check acl value
        arequal_checksum_before = redant.collect_mounts_arequal(self.mounts[0])
        self._check_acl_set_to_files()

        # Add brick to volume
        ret = redant.expand_volume(self.server_list[0],
                                   self.vol_name, self.server_list,
                                   self.brick_roots, force=True)
        if not ret:
            raise Exception("Failed to expand volume")

        # Trigger rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0],
                               force=True)

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=1200)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Check acl value if it's same as before rebalance
        self._check_acl_set_to_files()

        # Check for data loss by comparing arequal before and after ops
        arequal_checksum_after = redant.collect_mounts_arequal(self.mounts[0])
        if arequal_checksum_before != arequal_checksum_after:
            raise Exception("arequal checksum in NOT equal")
