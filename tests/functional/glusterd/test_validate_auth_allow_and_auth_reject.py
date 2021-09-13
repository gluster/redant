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
Tests to validate auth.allow and auth.reject on a volume
"""

# disruptive;rep,dist,dist-rep,dist-disp,arb,dist-arb

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 self.vol_type_inf[self.volume_type],
                                 self.server_list, self.brick_roots)

        # Create mountpoints
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])

    def _set_option_and_unmount_and_mount_volumes(self, redant, option="",
                                                  is_allowed=True):
        """
        Setting volume option and then mounting and unmounting the volume
        """
        # Check if an option is passed
        if option:
            # Setting the option passed as an argument
            redant.set_volume_options(self.vol_name,
                                      {option: self.client_list[0]},
                                      self.server_list[0])

        # Mounting a volume
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0], False)

        ret = redant.is_mounted(self.vol_name, self.mountpoint,
                                self.client_list[0], self.server_list[0])

        if is_allowed and not ret:
            raise Exception("Unexpected: Volume mount failed. "
                            f"Error: {ret['error_msg']}")

        elif not is_allowed and ret:
            raise Exception("Unexpected: Volume mount should have failed")

        # Unmount only if the volume is supposed to be mounted
        if is_allowed:
            redant.volume_unmount(self.vol_name, self.mountpoint,
                                  self.client_list[0])

    def _check_validate_test(self, redant):
        """
        Checking volume mounting and unmounting with auth.allow
        and auth.reject option set for it
        """
        # Setting auth.allow option and then mounting and unmounting volume
        self._set_option_and_unmount_and_mount_volumes(redant, "auth.allow")

        # Reseting the volume options
        redant.volume_reset(self.vol_name, self.server_list[0])

        # Setting auth.reject option and then checking mounting of volume
        self._set_option_and_unmount_and_mount_volumes(redant,
                                                       "auth.reject",
                                                       False)

        # Reseting the volume options
        redant.volume_reset(self.vol_name, self.server_list[0])

        # Check mounting and unmounting of volume without setting any options
        self._set_option_and_unmount_and_mount_volumes(redant)

    def run_test(self, redant):
        """
        Test Case:
        1. Create and start a volume
        2. Disable brick mutliplex
        2. Set auth.allow option on volume for the client address on which
           volume is to be mounted
        3. Mount the volume on client and then unmmount it.
        4. Reset the volume
        5. Set auth.reject option on volume for the client address on which
           volume is to be mounted
        6. Mounting the volume should fail
        7. Reset the volume and mount it on client.
        8. Repeat the steps 2-7 with brick multiplex enabled

        """

        # Setting cluster.brick-multiplex to disable
        redant.set_volume_options('all',
                                  {'cluster.brick-multiplex': 'disable'},
                                  self.server_list[0])

        # Checking auth options with brick multiplex disabled
        self._check_validate_test(redant)

        # Setting cluster.brick-multiplex to enable
        redant.set_volume_options('all',
                                  {'cluster.brick-multiplex': 'enable'},
                                  self.server_list[0])
        # Checking auth options with brick multiplex enabled

        self._check_validate_test(redant)
