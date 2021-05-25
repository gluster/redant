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

    def _set_option_and_mount_and_unmount_volumes(self, redant, option="",
                                                  is_allowed=True):
        """
        Setting volume option and then mounting and unmounting the volume
        """
        mount_det = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Check if an option is passed
        if option:
            # Setting the option passed as an argument
            redant.set_volume_options(self.vol_name,
                                      {option: mount_det[0]['client']},
                                      self.server_list[0])

        # # Unmount only if the volume is supposed to be mounted
        if is_allowed:
            redant.volume_unmount(self.vol_name,
                                  mount_det[0]['mountpath'],
                                  mount_det[0]['client'])

        # Mounting a volume
        try:
            redant.volume_mount(self.server_list[0], self.vol_name,
                                mount_det[0]['mountpath'],
                                mount_det[0]['client'])
        except Exception as error:
            if is_allowed:
                raise Exception from error
            else:
                redant.logger.info(f"Expected: {error}")

    def _reset_the_volume(self, redant):
        """
        Resetting the volume
        """
        redant.volume_reset(self.vol_name, self.server_list[0])

    def _check_validate_test(self, redant):
        """
        Checking volume mounting and unmounting with auth.allow
        and auth.reject option set for it
        """
        # Setting auth.allow option and then mounting and unmounting volume
        self._set_option_and_mount_and_unmount_volumes(redant, "auth.allow")

        # # Reseting the volume options
        self._reset_the_volume(redant)

        # # Setting auth.reject option and then checking mounting of volume
        self._set_option_and_mount_and_unmount_volumes(redant,
                                                       "auth.reject",
                                                       False)

        # # Reseting the volume options
        self._reset_the_volume(redant)

        # # Check mounting and unmounting of volume without setting any options
        self._set_option_and_mount_and_unmount_volumes(redant)

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
