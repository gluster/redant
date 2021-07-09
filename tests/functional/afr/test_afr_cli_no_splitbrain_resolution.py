"""
Copyright (C) 2017-2021  Red Hat, Inc. <http://www.redhat.com>

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
    This test case runs split-brain resolution
    on a 5 files in split-brain on a 1x2 volume.
    After resolving split-brain, it makes sure that
    split brain resolution doesn't work on files
    already in split brain.
"""


# disruptive;rep

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = self.vol_type_inf['rep']
        conf_hash['replica_count'] = 2
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.proc,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):

        self.proc = []
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        if not (redant.
                disable_self_heal_daemon(self.vol_name, self.server_list[0])):
            raise Exception("Unable to disable self heal daemon")

        # getting list of all bricks
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if all_bricks is None:
            raise Exception("Unable to get all bricks list")

        if not redant.bring_bricks_offline(self.vol_name, all_bricks[0]):
            raise Exception(f"unable to bring {all_bricks[0]} offline")

        if not redant.are_bricks_offline(self.vol_name,
                                         all_bricks[0],
                                         self.server_list[0]):
            raise Exception(f"{all_bricks[0]} is still online")

        self.proc = (self.redant.
                     create_files(num_files=5,
                                  fix_fil_size="1k",
                                  path=self.mnt_list[0]['mountpath'],
                                  node=self.mnt_list[0]['client'],
                                  base_file_name="test_file"))
        ret = self.redant.validate_io_procs(self.proc, self.mnt_list[0])
        if not ret:
            raise Exception("IO validation failed")

        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          [all_bricks[0]]):
            raise Exception(f"Unable to bring {all_bricks[0]} online")
        if not redant.are_bricks_online(self.vol_name, [all_bricks[0]],
                                        self.server_list[0]):
            raise Exception(f"Brick {all_bricks[0]} is not online.")

        if not redant.bring_bricks_offline(self.vol_name, all_bricks[1]):
            raise Exception(f"unable to bring {all_bricks[1]} offline")

        if not redant.are_bricks_offline(self.vol_name,
                                         all_bricks[1],
                                         self.server_list[0]):
            raise Exception(f"{all_bricks[1]} is still online")

        self.proc = (self.redant.
                     create_files(num_files=5,
                                  fix_fil_size="10k",
                                  path=self.mnt_list[0]['mountpath'],
                                  node=self.mnt_list[0]['client'],
                                  base_file_name="test_file"))
        ret = self.redant.validate_io_procs(self.proc, self.mnt_list[0])
        if not ret:
            raise Exception("IO validation failed")

        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          [all_bricks[1]]):
            raise Exception(f"Unable to bring {all_bricks[1]} online")
        if not redant.are_bricks_online(self.vol_name, [all_bricks[1]],
                                        self.server_list[0]):
            raise Exception(f"Brick {all_bricks[1]} is not online.")

        if not redant.enable_self_heal_daemon(self.vol_name,
                                              self.server_list[0]):
            raise Exception("Failed to enable self heal daemon")

        if not (redant.
                is_volume_in_split_brain(self.server_list[0],
                                         self.vol_name)):
            raise Exception("unable to create split-brain scenario")

        redant.logger.info("resolving split-brain by choosing first "
                           "brick as the source brick")
        node, brick_path = all_bricks[0].split(':')
        for fcount in range(5):
            command = (f"gluster vol heal {self.vol_name} split-brain "
                       f"source-brick {all_bricks[0]} /test_file"
                       f"{str(fcount)}.txt")
            redant.execute_abstract_op_node(command, node)

        # triggering heal
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception("Failed to trigger heal")

        # waiting for heal to complete
        if not (redant.
                monitor_heal_completion(self.server_list[0],
                                        self.vol_name,
                                        timeout_period=240)):
            raise Exception("Heal not completed")

        # checking if file is in split-brain
        if (redant.
            is_volume_in_split_brain(self.server_list[0],
                                     self.vol_name)):
            raise Exception("File still in split-brain")

        node, _ = all_bricks[0].split(':')
        command = (f"gluster volume heal {self.vol_name} split-brain "
                   f"source-brick {all_bricks[1]} /test_file0.txt")
        ret = redant.execute_abstract_op_node(command, node, False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: split-brain resolution "
                            "command is successful on a file which"
                            " is not in split-brain")

        for fcount in range(5):
            fpath = (f"{self.mountpoint}/test_file{str(fcount)}.txt")
            status = redant.get_fattr(fpath, 'replica.split-brain-status',
                                      self.client_list[0], encode="text")
            status = status[1].split('=')[1].rstrip("\n")
            compare_string = ("\"The file is not under data or metadata "
                              "split-brain\"")

            if compare_string != status:
                raise Exception(f"file test_file{str(fcount)} is under"
                                " split-brain")
