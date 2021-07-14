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
    Validate absence of `healed` and `heal-failed` options
"""

# disruptive;rep
# TODO: nfs

import traceback
from random import choice
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.list_of_procs,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        - Create and mount a replicated volume
        - Kill one of the bricks and write IO from mount point
        - Verify `gluster volume heal <volname> info healed` and `gluster
          volume heal <volname> info heal-failed` command results in error
        - Validate `gluster volume help` doesn't list `healed` and
          `heal-failed` commands
        """

        self.list_of_procs = []
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Kill one of the bricks in the volume
        bricks_list = redant.get_online_bricks_list(self.vol_name,
                                                    self.server_list[0])
        if bricks_list is None:
            raise Exception("Unable to get the bricks list")

        random_brick = choice(bricks_list)
        redant.bring_bricks_offline(self.vol_name, random_brick)
        if not redant.are_bricks_offline(self.vol_name, [random_brick],
                                         self.server_list[0]):
            raise Exception(f"Brick {random_brick} is not offline.")

        proc = (redant.
                create_deep_dirs_with_files(self.mnt_list[0]['mountpath'],
                                            1, 10, 1, 1, 50,
                                            self.mnt_list[0]['client']))
        self.list_of_procs.append(proc)
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # Verify `gluster volume heal <volname> info healed` results in error
        cmd = 'gluster volume heal <volname> info'
        ret = redant.heal_info_healed(self.vol_name, self.server_list[0],
                                      False)
        if ret['error_code'] == 0:
            raise Exception(f"`{cmd} healed` should result in error.")

        if 'Usage' not in ret['error_msg']:
            raise Exception(f"`{cmd} healed` should list 'Usage'")

        # Verify `gluster volume heal <volname> info heal-failed` errors out
        ret = redant.heal_info_heal_failed(self.vol_name, self.server_list[0],
                                           False)
        if ret['error_code'] == 0:
            raise Exception(f"`{cmd} heal-failed` should result in error.")

        if 'Usage' not in ret['error_msg']:
            raise Exception(f"`{cmd} heal-failed` should list 'Usage'")

        # Verify absence of `healed` nd `heal-failed` commands in `volume help`
        cmd = 'gluster volume help | grep -i heal'
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])

        if 'healed' in ret['msg']:
            raise Exception(f'`healed` string shoulf not exist in {cmd}')

        if 'heal-failed' in ret['msg']:
            raise Exception(f'`healed` string shoulf not exist in {cmd}')
