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
    Test cases in this module tests whether directory with null gfid
    is getting the gfids assigned on both the subvols of a dist-rep
    volume when lookup comes on that directory from the mount point.
"""

# nonDisruptive;rep,dist-rep,dist

from time import sleep
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def verify_gfid_and_retun_gfid(self, dirname):
        dir_gfids = dict()
        for brick in self.bricks_list:
            brick_node, brick_path = brick.split(":")

            ret = self.redant.get_fattr(f'{brick_path}/{dirname}',
                                        'trusted.gfid', brick_node)
            if ret is not None:
                dir_gfids.setdefault(dirname, []).append(ret)
            else:
                raise Exception("trusted.gfid is not present on"
                                f"{brick}/{dirname}")

        # for value in dir_gfids[dirname]:
        if not (all(value[1] == dir_gfids[dirname][0][1]
                for value in dir_gfids[dirname])):
            raise Exception("gfid mismatched")

        return dir_gfids[dirname][0][1]

    def run_test(self, redant):
        """
        - Create a volume and mount it.
        - Create a directory on mount and check whether all the bricks have
          the same gfid.
        - Now delete gfid attr from all but one backend bricks,
        - Do lookup from the mount.
        - Check whether all the bricks have the same gfid assigned.
        """

        # Create a directory on the mount
        redant.create_dir(self.mountpoint, "dir1", self.client_list[0])

        # Verify gfids are same on all the bricks and get dir1 gfid
        self.bricks_list = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        dir_gfid = self.verify_gfid_and_retun_gfid("dir1")

        # Delete gfid attr from all but one backend bricks
        for brick in self.bricks_list[1:]:
            brick_node, brick_path = brick.split(":")
            redant.delete_fattr(f'{brick_path}/dir1',
                                'trusted.gfid',
                                brick_node)

        # Trigger heal from mount point
        redant.trigger_heal_full(self.vol_name, self.server_list[0])
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Heal not yet finished")
        sleep(10)
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        redant.get_mounts_stat(self.mnt_list)

        # Verify that all gfids for dir1 are same and get the gfid
        dir_gfid_new = self.verify_gfid_and_retun_gfid("dir1")
        if not all(gfid in dir_gfid for gfid in dir_gfid_new):
            raise Exception('Previous gfid and new gfid are not equal, '
                            'which is not expected, previous gfid '
                            f'{dir_gfid} and new gfid {dir_gfid_new}')
