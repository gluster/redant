"""
 Copyright (C) 2021  Red Hat, Inc. <http://www.redhat.com>

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
    Test cases in this module tests the authentication allow feature
"""

# disruptive;dist-rep,dist-disp
from tests.d_parent_test import DParentTest


class TestFuseAuthAllow(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Create and start the volume
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node("mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)

    def _add_brick_rebalance(self):
        """
        Create files,Perform Add brick and wait for rebalance to complete
        """
        # Create files on mount point using dd command
        cmd = (f"cd {self.mountpoint};for i in "
               "{1..10000};do dd if=/dev/urandom bs=1024 count=1 "
               "of=file$i;done;")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Add brick to volume
        if not self.redant.expand_volume(self.server_list[0], self.vol_name,
                                         self.server_list, self.brick_roots):
            raise Exception("Failed to expand volume")

        # Trigger rebalance and wait for it to complete
        self.redant.rebalance_start(self.vol_name, self.server_list[0],
                                    force=True)

        # Wait for rebalance to complete
        if not self.redant.wait_for_rebalance_to_complete(self.vol_name,
                                                          self.server_list[0],
                                                          timeout=1200):
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

    def run_test(self, redant):
        """
        Validating the FUSE authentication volume options with rebalance
        Steps:
        1. Setup and start volume
        2. Set auth.allow on volume for client1 using ip of client1
        3. Mount volume on client1.
        4. Create files on mount point using dd command
        5. Perform add brick operation
        6. Trigger rebalance
        7. Set auth.allow on volume for client1 using hostname of client1.
        8. Repeat steps from 3 to 7
        """
        # Setting authentication on volume for client1 using ip
        auth_dict = {'all': [self.client_list[0]]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mounting volume on client1
        redant.authenticated_mount(self.vol_name, self.server_list[0],
                                   self.mountpoint, self.client_list[0])

        # Create files,perform add-brick,trigger rebalance
        self._add_brick_rebalance()

        # Unmount volume from client1
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])

        # Obtain hostname of client1
        ret = redant.execute_abstract_op_node("hostname", self.client_list[0])
        hostname_client1 = ret['msg'][0].rstrip('\n')

        # Setting authentication on volume for client1 using hostname
        auth_dict = {'all': [hostname_client1]}
        if not redant.set_auth_allow(self.vol_name, self.server_list[0],
                                     auth_dict):
            raise Exception("Failed to set authentication")

        # Mounting volume on client1
        self.authenticated_mount(self.vol_name, self.server_list[0],
                                 self.mountpoint, self.client_list[0])

        # Create files,perform add-brick and trigger rebalance
        self._add_brick_rebalance()
