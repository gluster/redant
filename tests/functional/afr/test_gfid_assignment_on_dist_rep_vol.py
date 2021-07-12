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
# nonDisruptive;dist-rep

import time
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def verify_gfid(self, dirname):
        dir_gfids = dict()
        self.bricks_list = self.redant.get_all_bricks(self.vol_name,
                                                      self.server_list[0])
        for brick in self.bricks_list:
            brick_node, brick_path = brick.split(":")

            ret = self.redant.get_fattr(f'{brick_path}/{dirname}',
                                        'trusted.gfid',
                                        brick_node)
            if ret is None:
                raise Exception("trusted.gfid is not present on"
                                f"{brick}/{dirname}")
            dir_gfids.setdefault(dirname, []).append(ret)

        for each in dir_gfids[dirname]:
            if each[1] != dir_gfids[dirname][0][1]:
                raise Exception("gfid mismatched")

    def run_test(self, redant):
        """
        - Create a dis-rep volume and mount it.
        - Create a directory on mount and check whether all the bricks have
          the same gfid.
        - On the backend create a new directory on all the bricks.
        - Do lookup from the mount.
        - Check whether all the bricks have the same gfid assigned.
        """
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Enable client side healing
        options = {"metadata-self-heal": "on",
                   "entry-self-heal": "on",
                   "data-self-heal": "on"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Create a directory on the mount
        path_dir = f"{self.mnt_list[0]['mountpath']}/dir1"
        redant.logger.info("Creating directory")
        self.proc = (redant.
                     create_deep_dirs_with_files(path_dir,
                                                 1, 1, 0, 1, 0,
                                                 self.mnt_list[0]['client']))
        ret = redant.validate_io_procs([self.proc], self.mnt_list[0])
        if not ret:
            raise Exception("IO validation failed")

        # Verify gfids are same on all the bricks
        self.verify_gfid("dir1")

        # Create a new directory on all the bricks directly
        for brick in self.bricks_list:
            brick_node, brick_path = brick.split(":")

            redant.execute_abstract_op_node(f"mkdir {brick_path}/dir2",
                                            brick_node)

        # To circumvent is_fresh_file() check in glusterfs code.
        time.sleep(2)

        # Do a clinet side lookup on the new directory and verify the gfid
        # All the bricks should have the same gfid assigned
        redant.execute_abstract_op_node((f"ls {self.mnt_list[0]['mountpath']}"
                                         "/dir2"),
                                        self.mnt_list[0]['client'])

        # Verify gfid is assigned on all the bricks and are same
        self.verify_gfid("dir2")
