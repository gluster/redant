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

    # def verify_gfid(self, dirname):
    #     dir_gfids = dict()
    #     bricks_list = get_all_bricks(self.mnode, self.volname)
    #     for brick in bricks_list:
    #         brick_node, brick_path = brick.split(":")

    #         ret = get_fattr(brick_node, '%s/%s' % (brick_path, dirname),
    #                         'trusted.gfid')
    #         self.assertIsNotNone(ret, "trusted.gfid is not present on"
    #                              "%s/%s" % (brick, dirname))
    #         dir_gfids.setdefault(dirname, []).append(ret)

    #         for key in dir_gfids:
    #             self.assertTrue(all(value == dir_gfids[key][0]
    #                                 for value in dir_gfids[key]),
    #                             "gfid mismatch for %s" % dirname)

    def run_test(self, redant):
        """
        - Create a dis-rep volume and mount it.
        - Create a directory on mount and check whether all the bricks have
          the same gfid.
        - On the backend create a new directory on all the bricks.
        - Do lookup from the mount.
        - Check whether all the bricks have the same gfid assigned.
        """
        # Enable client side healing
        options = {"metadata-self-heal": "on",
                   "entry-self-heal": "on",
                   "data-self-heal": "on"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # # Create a directory on the mount
        # g.log.info("Creating a directory")
        # cmd = "/usr/bin/env python %s create_deep_dir -d 0 -l 0 %s/dir1 " % (
        #     self.script_upload_path,
        #     self.mounts[0].mountpoint)
        # ret, _, _ = g.run(self.clients[0], cmd)
        # self.assertEqual(ret, 0, "Failed to create directory on mountpoint")
        # g.log.info("Directory created successfully on mountpoint")

        # # Verify gfids are same on all the bricks
        # self.verify_gfid("dir1")

        # # Create a new directory on all the bricks directly
        # bricks_list = get_all_bricks(self.mnode, self.volname)
        # for brick in bricks_list:
        #     brick_node, brick_path = brick.split(":")

        #     ret, _, _ = g.run(brick_node, "mkdir %s/dir2" % (brick_path))
        #     self.assertEqual(ret, 0, "Failed to create directory on brick %s"
        #                      % (brick))

        # # To circumvent is_fresh_file() check in glusterfs code.
        # time.sleep(2)

        # # Do a clinet side lookup on the new directory and verify the gfid
        # # All the bricks should have the same gfid assigned
        # ret, _, _ = g.run(self.clients[0], "ls %s/dir2"
        #                   % self.mounts[0].mountpoint)
        # self.assertEqual(ret, 0, "Lookup on directory \"dir2\" failed.")
        # g.log.info("Lookup on directory \"dir2\" successful")

        # # Verify gfid is assigned on all the bricks and are same
        # self.verify_gfid("dir2")
