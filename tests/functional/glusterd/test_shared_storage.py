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
   Test cases in this module related glusterd enabling and
   disabling shared storage
"""

from random import choice
from tests.d_parent_test import DParentTest

# disruptive;dist


class TestSharedStorage(DParentTest):

    def _enable_and_check_shared_storage(self):
        """Enable and check shared storage is present"""

        ret = self.redant.enable_shared_storage(self.server_list[0])
        if not ret:
            raise Exception("Failed to enable shared storage volume")

        # Check volume list to confirm gluster_shared_storage is created
        ret = self.redant.check_gluster_shared_volume(self.server_list[0])
        if not ret:
            raise Exception("gluster_shared_storage volume not created after"
                            " enabling it")

    def _disable_and_check_shared_storage(self):
        """Disable a shared storage without specifying the domain and check"""

        ret = self.redant.disable_shared_storage(self.server_list[0])
        if not ret:
            raise Exception("Failed to disable shared storage volume")

        # Check volume list to confirm gluster_shared_storage is created
        ret = self.redant.check_gluster_shared_volume(self.server_list[0],
                                                      False)
        if not ret:
            raise Exception("gluster_shared_storage volume not deleted after"
                            " disabling it")

    def _is_shared_storage_mounted_on_the_nodes(self, brick_details, mounted):
        """
        Checks if the shared storage is mounted on the nodes where it is
        created.
        """
        for brick in brick_details:
            ret = self.redant.is_shared_volume_mounted(brick.split(":")[0])
            if mounted and not ret:
                raise Exception("Shared volume not mounted even after "
                                "enabling it")
            elif not mounted and ret:
                raise Exception("Shared volume not unmounted even"
                                " after disabling it")

    def _get_all_bricks(self):
        """Get all bricks where the shared storage is mounted"""

        brick_list = self.redant.get_all_bricks("gluster_shared_storage",
                                                self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get the brick list")

        return brick_list

    def _shared_storage_test_without_node_reboot(self):
        """Shared storge testcase till the node reboot scenario"""

        # Enable shared storage and check it is present on the cluster
        self._enable_and_check_shared_storage()

        # Get all the bricks where shared storage is mounted
        brick_list = self._get_all_bricks()

        # Check the shared volume is mounted on the nodes where it is created
        self._is_shared_storage_mounted_on_the_nodes(brick_list, True)

        # Disable shared storage and check it is not present on the cluster
        self._disable_and_check_shared_storage()

        # Check the shared volume is unmounted on the nodes where it is created
        self._is_shared_storage_mounted_on_the_nodes(brick_list, False)

        # Create a volume with name gluster_shared_storage
        volume = "gluster_shared_storage"
        conf_hash = {
            "replicated": {
                "dist_count": 1,
                "replica_count": 2,
                "transport": "tcp"
            }
        }
        self.redant.volume_create(volume, self.server_list[0],
                                  conf_hash, self.server_list,
                                  self.brick_roots, True)

        # Disable the shared storage should fail
        ret = self.redant.disable_shared_storage(self.server_list[0])
        if ret:
            raise Exception("Unexpected: Successfully disabled shared"
                            " storage")

        # Check volume list to confirm gluster_shared_storage
        # is not deleted which was created before
        vol_list = self.redant.get_volume_list(self.server_list[0])
        if vol_list is None:
            raise Exception("Failed to get volume list")

        if "gluster_shared_storage" not in vol_list:
            raise Exception("gluster_shared_storage volume got"
                            " deleted after disabling it")

        # Delete the volume created
        self.redant.volume_delete(volume, self.server_list[0])

        # Enable shared storage and check it is present on the cluster
        self._enable_and_check_shared_storage()

        # Check the shared volume is mounted on the nodes where it is created
        self._is_shared_storage_mounted_on_the_nodes(brick_list, True)

        # Disable shared storage and check it is not present on the cluster
        self._disable_and_check_shared_storage()

        # Check the shared volume is unmounted on the nodes where it is created
        self._is_shared_storage_mounted_on_the_nodes(brick_list, False)

    def run_test(self, redant):
        """
        This test case includes:
        -> Enable a shared storage
        -> Disable a shared storage
        -> Create volume of any type with
           name gluster_shared_storage
        -> Disable the shared storage
        -> Check, volume created in step-3 is
           not deleted
        -> Delete the volume
        -> Enable the shared storage
        -> Check volume with name gluster_shared_storage
           is created
        -> Disable the shared storage
        -> Enable shared storage and validate whether it is mounted
        -> Perform node reboot
        -> Post reboot validate the bricks are mounted back or not
        """
        self._shared_storage_test_without_node_reboot()

        # Enable shared storage and check it is present on the cluster
        self._enable_and_check_shared_storage()

        # Get all the bricks where shared storage is mounted
        brick_list = self._get_all_bricks()

        # Check the shared volume is mounted on the nodes where it is created
        self._is_shared_storage_mounted_on_the_nodes(brick_list, True)

        # Perform node reboot on any of the nodes where the shared storage is
        # mounted
        node_to_reboot = choice(brick_list)
        node_to_reboot = node_to_reboot.split(":")[0]
        redant.reboot_nodes(node_to_reboot)
        if not redant.wait_node_power_up(node_to_reboot):
            raise Exception("Node has not come up after reboot")

        # Post reboot checking peers are connected
        if not redant.wait_till_all_peers_connected(self.server_list):
            raise Exception("Peers are not connected after node reboot")

        # Check the shared volume is mounted on the nodes where it is created
        self._is_shared_storage_mounted_on_the_nodes(brick_list, True)

        # Disable shared storage and check it is not present on the cluster
        self._disable_and_check_shared_storage()

        # Check the shared volume is unmounted on the nodes where it is created
        self._is_shared_storage_mounted_on_the_nodes(brick_list, False)
