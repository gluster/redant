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
    Test mount point ownership persistence post volume restart.
"""

# nonDisruptive;dist,rep,dist-rep,disp,dist-disp,dist-arb

from time import sleep
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def _validate_mount_permissions(self):
        """
        Verify the mount permissions
        """
        stat_mountpoint_dict = (self.redant.
                                get_file_permission(self.client_list[0],
                                                    self.mountpoint))

        if stat_mountpoint_dict['file_perm'] != 777:
            raise Exception(f"Expected 777 but found "
                            f"{stat_mountpoint_dict['file_perm']}")

    def run_test(self, redant):
        """
        Test mountpoint ownership post volume restart
        1. Create a volume and mount it on client.
        2. set ownsership permissions and validate it.
        3. Restart volume.
        4. Ownership permissions should persist.
        """
        # Set full permissions on the mountpoint.
        ret = redant.set_file_permissions(self.client_list[0], self.mountpoint,
                                          "-R 777")
        if not ret:
            raise Exception("Failed to set permissions on the mountpoint")

        # # Validate the permissions set.
        self._validate_mount_permissions()

        # Stop the volume.
        redant.volume_stop(self.vol_name, self.server_list[0])

        # Start the volume.
        redant.volume_start(self.vol_name, self.server_list[0])

        # Wait for all volume processes to be up and running.
        if not (redant.
                wait_for_volume_process_to_be_online(self.vol_name,
                                                     self.server_list[0],
                                                     self.server_list)):
            raise Exception("All volume processes are not up")
        # Adding sleep for the mount to be recognized by client.
        sleep(3)

        # validate the mountpoint permissions.
        self._validate_mount_permissions()
