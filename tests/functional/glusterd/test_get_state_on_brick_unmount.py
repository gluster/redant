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

Description:
    Tests to verify 'gluster get state' command on unmounting the brick from
    an online volume
"""
# disruptive;rep,dist,dist-rep,disp,dist-disp,arb,dist-arb

from random import choice
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        # Mount the bricks which are unmounted as part of test
        if getattr(self, 'umount_host', None) and getattr(self, 'umount_brick',
                                                          None):
            self.redant.execute_abstract_op_node('mount -a',
                                                 self.umount_host)

        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1. Form a gluster cluster by peer probing and create a volume
        2. Unmount the brick using which the volume is created
        3. Run 'gluster get-state' and validate absence of error 'Failed to get
           daemon state. Check glusterd log file for more details'
        4. Create another volume and start it using different bricks which are
           not used to create above volume
        5. Run 'gluster get-state' and validate the absence of above error.
        """
        # Select one of the bricks in the volume to unmount
        brick_list = redant.get_all_bricks(self.vol_name,
                                           self.server_list[0])
        if brick_list is None:
            raise Exception("Bricks list is empty")

        select_brick = choice(brick_list[1:])
        self.umount_host, self.umount_brick = (
            select_brick.split(':'))

        # Verify mount entry in /etc/fstab
        ret = redant.check_if_pattern_in_file(self.umount_host,
                                              self.umount_brick,
                                              '/etc/fstab')
        if ret != 0:
            raise Exception("Brick mount entry not found in"
                            f"/etc/fstab of {self.umount_host}")
        # Unmount the selected brick
        cmd = f'umount {self.umount_brick}'
        redant.execute_abstract_op_node(cmd, self.umount_host)

        # Run 'gluster get-state' and verify absence of any error
        redant.get_state(self.server_list[0])
        # Create another volume
        self.volume_name1 = 'second_volume'
        self.volume_type1 = 'dist-rep'
        conf_dict = self.vol_type_inf[self.conv_dict[self.volume_type1]]

        redant.setup_volume(self.volume_name1, self.server_list[0],
                            conf_dict, self.server_list,
                            self.brick_roots, True)
        # Run 'gluster get-state' and verify absence of any error after
        # creation of second-volume
        redant.get_state(self.server_list[0])
