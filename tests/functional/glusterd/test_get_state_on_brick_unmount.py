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

from glusto.core import Glusto as g

from glustolibs.gluster.gluster_base_class import GlusterBaseClass, runs_on
from glustolibs.gluster.exceptions import ExecutionError
from glustolibs.gluster.volume_libs import (setup_volume, cleanup_volume,)
from glustolibs.gluster.volume_ops import (get_gluster_state, get_volume_list)
from glustolibs.gluster.brick_libs import get_all_bricks
from glustolibs.gluster.glusterfile import check_if_pattern_in_file


@runs_on([['distributed', 'replicated',
           'distributed-replicated',
           'dispersed', 'distributed-dispersed',
           'arbiter', 'distributed-arbiter'], []])
"""
# disruptive;rep

from random import choice
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    # def tearDown(self):

    #     # Mount the bricks which are unmounted as part of test
    #     if getattr(self, 'umount_host', None) and getattr(self, 'umount_brick',
    #                                                       None):
    #         ret, _, _ = g.run(self.umount_host, 'mount -a')
    #         if ret:
    #             raise ExecutionError("Not able to mount unmounted brick on "
    #                                  "{}".format(self.umount_host))

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
        print(f"Bricks: \n {brick_list}\n")
        if brick_list is None:
            raise Exception("Bricks list is empty")

        select_brick = choice(brick_list[1:])
        print(f"\nselect brick: {select_brick}\n")
        self.umount_host, self.umount_brick = (
            select_brick.split(':'))
        print(f"Host:{self.umount_host}\nBrick:{self.umount_brick}\n")

        # Verify mount entry in /etc/fstab
        ret = redant.check_if_pattern_in_file(self.umount_host,
                                              self.umount_brick, '/etc/fstab')
        if ret != 0:
            raise Exception("Brick mount entry not found in"
                            f"/etc/fstab of {self.umount_host}")
        # Unmount the selected brick
        # cmd = f'umount {self.umount_brick}'
        # redant.execute_abstract_op_node(cmd, self.umount_host)

        # # Run 'gluster get-state' and verify absence of any error
        # ret = get_gluster_state(self.mnode)
        # self.assertIsNotNone(ret, "Fail: 'gluster get-state' didn't dump the "
        #                      "state of glusterd when {} unmounted from "
        #                      "{}".format(self.umount_brick, self.umount_host))

        # # Create another volume
        # self.volume['name'] = 'second_volume'
        # ret = setup_volume(self.mnode, self.all_servers_info, self.volume)
        # self.assertTrue(ret, 'Failed to create and start volume')
        # g.log.info('Second volume created and started successfully')

        # # Run 'gluster get-state' and verify absence of any error after
        # # creation of second-volume
        # ret = get_gluster_state(self.mnode)
        # self.assertIsNotNone(ret, "Fail: 'gluster get-state' didn't dump the "
        #                      "state of glusterd ")
