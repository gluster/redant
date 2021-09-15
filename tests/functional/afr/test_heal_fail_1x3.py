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
    This test case verifies the gfid self-heal on a 1x3
    replicate volume.
"""

# disruptive;rep
# TODO: nfs, cifs

import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        try:
            ret = self.redant.wait_for_io_to_complete(self.all_mounts_procs,
                                                      self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        1. file created at mount point
        2. 2 bricks brought down
        3. file deleted
        4. created a new file from the mount point
        5. all bricks brought online
        6. check if gfid worked correctly
        """

        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        options = {"cluster.quorum-type": "fixed"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        for mount_obj in self.mounts:
            proc = redant.create_files('10k', mount_obj['mountpath'],
                                       mount_obj['client'],
                                       base_file_name='test_file')
            self.all_mounts_procs.append(proc)
        # Validate I/O
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("Failed to validate IO")

        # getting list of all bricks
        all_bricks = redant.get_all_bricks(self.vol_name,
                                           self.server_list[0])
        if all_bricks is None:
            raise Exception("Failed to get all the bricks")

        redant.bring_bricks_offline(self.vol_name, all_bricks[:2])
        if not redant.are_bricks_offline(self.vol_name, all_bricks[:2],
                                         self.server_list[0]):
            raise Exception(f"Bricks {all_bricks[:2]} not all offline.")

        command = f"rm -f {self.mounts[0]['mountpath']}/test_file0.txt"
        redant.logger.info("Deleting the file on the mountpoint")
        redant.execute_abstract_op_node(command,
                                        self.mounts[0]['client'])

        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            proc = redant.create_files('1M', mount_obj['mountpath'],
                                       mount_obj['client'],
                                       base_file_name='test_file')
            self.all_mounts_procs.append(proc)
        # Validate I/O
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("Failed to validate IO")

        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   all_bricks[:2])
        if not redant.are_bricks_online(self.vol_name, all_bricks[:2],
                                        self.server_list[0]):
            raise Exception(f"Bricks {all_bricks[:2]} not online.")

        redant.get_file_stat(self.mounts[0]['client'],
                             f"{self.mounts[0]['mountpath']}/test_file0.txt")

        # check if heal is complete
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        # Check arequals on all the bricks
        arequals = redant.collect_mounts_arequal(self.mounts)
        mount_point_total = arequals[0][-1].split(':')[-1]

        # Get arequal on bricks and compare with mount_point_total
        arequals = redant.collect_bricks_arequal(all_bricks)
        for arequal in arequals:
            brick_total = arequal[-1].split(':')[-1]
            if mount_point_total != brick_total:
                raise Exception('Arequals for mountpoint and brick '
                                'are not equal')

        # checking file size of healed file on each brick to verify
        # correctness of choice for sink and source
        for brick in all_bricks:
            node, brick_path = brick.split(':')
            stat_dict = redant.get_file_stat(node,
                                             f"{brick_path}/test_file0.txt")
            if stat_dict['msg']['st_size'] != 1048576:
                raise Exception("File size of healed file is different"
                                " than expected.")
