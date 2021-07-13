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
        """
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
        """
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

        (redant.
         execute_abstract_op_node(("touch "
                                   f"{self.mnt_list[0]['mountpath']}/dir2"),
                                  self.client_list[0]))

        ret = (redant.
               execute_abstract_op_node(("mkdir "
                                         f"{self.mnt_list[0]['mountpath']}"
                                         "/dir3"), self.client_list[0], False))
        if ret['error_code'] == 0:
            raise Exception("Creation of directory with same name as "
                            "directory \"dir3\" was supposed to fail.")

        for number in range(1, 4):
            (redant.
             execute_abstract_op_node((f"ls {self.mnt_list[0]['mountpath']}"
                                       f"/dir{number}"), self.client_list[0]))
            (redant.
             execute_abstract_op_node((f"find {self.mnt_list[0]['mountpath']}"
                                       f"/dir{number}"), self.client_list[0]))

        if not (redant.
                monitor_heal_completion(self.server_list[0], self.vol_name)):
            raise Exception("Heal is not yet completed.")

        # Verify directories are present on the backend and gfids are assigned
        self.verify_gfid("dir1")
        self.verify_gfid("dir2")
        self.verify_gfid("dir3")

        # Check whether all the directories are listed on the mount
        ret = (redant.
               execute_abstract_op_node((f"ls {self.mnt_list[0]['mountpath']}"
                                         " | wc -l"), self.client_list[0]))
        if ret['msg'][0].rstrip("\n") != '3':
            raise Exception("Not all the directories are listed on the mount")
