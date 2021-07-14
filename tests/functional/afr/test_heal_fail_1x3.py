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

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

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

        # g.log.info("checking if the areequal checksum of all the bricks in "
        #            "the subvol match")
        # checksum_list = []
        # for brick in all_bricks:
        #     node, brick_path = brick.split(':')
        #     command = "arequal-checksum -p " + brick_path + \
        #               " -i .glusterfs -i .landfill"
        #     ret, out, _ = g.run(node, command)
        #     self.assertEqual(ret, 0, "unable to get the arequal checksum "
        #                              "of the brick")
        #     checksum_list.append(out)
        #     # checking file size of healed file on each brick to verify
        #     # correctness of choice for sink and source
        #     stat_dict = get_file_stat(node, brick_path + '/test_file0.txt')
        #     self.assertEqual(stat_dict['size'], '1048576',
        #                      "file size of healed file is different "
        #                      "than expected")
        # flag = all(val == checksum_list[0] for val in checksum_list)
        # self.assertTrue(flag, "the arequal checksum of all bricks is"
        #                 "not same")
        # g.log.info("the arequal checksum of all the bricks in the subvol "
        #            "is same")
