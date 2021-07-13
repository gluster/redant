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
    Test cases in this module tests whether directories with null gfid
    are getting the gfids assigned and directories get created on the
    remaining bricks when named lookup comes on those from the mount point.
"""

# nonDisruptive;rep

from time import sleep
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
        '''
        1) create replicate volume ( 1 * 3 )
        2. Test the case with default afr options.
        3. Test the case with volume option 'self-heal-daemon'
        4) create dirs on bricks from backend. lets say dir1, dir2 and dir3
        5) From mount point,
            echo "hi" >dir1 ->must fail
            touch dir2 --> must pass
            mkdir dir3 ->must fail
        6) From mount point,
            ls -l  and find, must list both dir1 and dir2 and dir3
        7) check on all backend bricks, dir1, dir2 and dir3 should be created
        8) heal info should show zero, and also gfid and other attributes
         must exist
        '''
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        options = {"metadata-self-heal": "on",
                   "entry-self-heal": "on",
                   "data-self-heal": "on"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        bricks_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        i = 0
        for brick in bricks_list:
            i += 1
            brick_node, brick_path = brick.split(":")
            redant.create_dir(brick_path, f"dir{i}", brick_node)

        # To circumvent is_fresh_file() check in glusterfs code.
        sleep(2)

        # Do named lookup on directories from mount
        cmd = f"echo Hi >  {self.mnt_list[0]['mountpath']}/dir1"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0],
                                              False)

        errmsg = f"bash: {self.mnt_list[0]['mountpath']}/dir1: Is a directory"
        if errmsg != ret['error_msg'].rstrip("\n"):
            raise Exception("Unexpected: Writing to a directory "
                            "was successfull")

        redant.execute_abstract_op_node(f"touch {self.mnt_list[0]['mountpath']}/dir2",
                                        self.client_list[0])

        # ret, _, err = g.run(self.clients[0], "mkdir %s/dir3"
        #                     % self.mounts[0].mountpoint)
        # self.assertNotEqual(ret, 0, "Creation of directory with same name as "
        #                     "directory \"dir3\" succeeded, which is not "
        #                     "supposed to.")
        # g.log.info("Creation of directory \"dir3\" failed as expected")

        # g.log.info("Do a named lookup on dirs")
        # for number in range(1, 4):
        #     ret, _, _ = g.run(self.clients[0], "ls %s/dir%s"
        #                       % (self.mounts[0].mountpoint, number))
        #     ret, _, _ = g.run(self.clients[0], "find %s/dir%s"
        #                       % (self.mounts[0].mountpoint, number))
        # g.log.info("Named lookup Successful")

        # # Check if heal is completed
        # counter = 0
        # while True:
        #     ret = is_heal_complete(self.mnode, self.volname)
        #     if ret or counter > 30:
        #         break
        #     counter += 1
        #     sleep(2)
        # self.assertTrue(ret, 'Heal is not complete')
        # g.log.info('Heal is completed successfully')

        # # Verify directories are present on the backend and gfids are assigned
        # self.verify_gfid("dir1")
        # self.verify_gfid("dir2")
        # self.verify_gfid("dir3")

        # # Check whether all the directories are listed on the mount
        # _, count, _ = g.run(self.clients[0], "ls %s | wc -l"
        #                     % self.mounts[0].mountpoint)
        # self.assertEqual(int(count), 3, "Not all the directories are listed on"
        #                  "the mount")
        # g.log.info("All the directories are listed on the mount.")
