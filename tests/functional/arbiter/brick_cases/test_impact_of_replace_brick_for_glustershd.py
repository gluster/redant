"""
Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module tests the self heal daemon process.
"""


# disruptive;arb,dist-arb
# TODO: nfs

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):

        replaced_bricks = []
        ret, pids = redant.get_self_heal_daemon_pid(self.server_list)
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process "
                            f"found : {pids}")
        glustershd_pids = pids
        # get the bricks for the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        # validate the bricks present in volume info with
        # glustershd server volume file
        if not (redant.
                do_bricks_exist_in_shd_volfile(self.vol_name,
                                               bricks_list,
                                               self.server_list[0])):
            raise Exception("Brick List from volume info is different "
                            "from glustershd server volume file. "
                            "Please check log file for details")
        # get the subvolumes
        subvols_list = redant.get_subvols(self.vol_name, self.server_list[0])

        # replace brick from each sub-vol
        for i in range(0, len(subvols_list)):
            subvol_brick_list = subvols_list[i]
            redant.logger.debug(f"sub-volume {i+1} "
                                f"brick list : {subvol_brick_list}")
            brick_to_replace = subvol_brick_list[-1]
            new_brick = brick_to_replace + 'new'
            redant.replace_brick(self.server_list[0],
                                 self.vol_name,
                                 brick_to_replace, new_brick)
            replaced_bricks.append(brick_to_replace)

        # Verify volume's all process are online for 60 sec
        if not (redant.
                wait_for_volume_process_to_be_online(self.vol_name,
                                                     self.server_list[0],
                                                     self.server_list,
                                                     timeout=60)):
            raise Exception("Volume processes not yet online")

        # Verify glustershd process releases its parent process
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process found")

        # check the self-heal daemon process
        ret, pids = redant.get_self_heal_daemon_pid(self.server_list)
        if not ret:
            raise Exception("Either No self heal daemon process found or "
                            "more than One self heal daemon process "
                            f"found : {pids}")
        glustershd_pids_after_replacement = pids

        # Compare pids before and after replacing
        if glustershd_pids == glustershd_pids_after_replacement:
            raise Exception("Self heal Daemon process is same before "
                            "and after replacing bricks")

        # get the bricks for the volume after replacing
        br_lis_aft_repl = redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
        if br_lis_aft_repl is None:
            raise Exception("Empty bricks list after replacing")

        # validate the bricks present in volume info
        # with glustershd server volume file after replacing bricks
        if not (redant.
                do_bricks_exist_in_shd_volfile(self.vol_name,
                                               br_lis_aft_repl,
                                               self.server_list[0])):
            raise Exception("Brick List from volume info is different "
                            "from glustershd server volume file after "
                            "replacing bricks. Please check log file "
                            "for details")
