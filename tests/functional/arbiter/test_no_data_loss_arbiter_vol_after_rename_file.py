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
    This test case deals with self-heal tests related to arbiter volume
    type.
"""

# disruptive;arb

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        - Create a 1x(2+1) arbiter replicate volume
        - Turn off Clients side healing option
        - Create a directory 'test_dir'
        - Bring down the 1-st data brick
        - Create a file under 'test_dir'
        - Bring down the 2-nd data brick
        - Bring up the 1-st data brick
        - Rename file under 'test_dir'
        - Bring up the 2-nd data brick
        - Turn on Clients side healing option
        - Trigger heal
        - Check if no pending heals
        - Check if md5sum on mountpoint is the same for md5sum_node on nodes
        """
        test_dir = 'test_dir'

        # Setting options
        options = {"cluster.metadata-self-heal": "off",
                   "cluster.entry-self-heal": "off",
                   "cluster.data-self-heal": "off"}

        redant.set_volume_options(self.vol_name, options, self.server_list[0])
        options_dict = redant.get_volume_options(self.vol_name,
                                                 node=self.server_list[0])
        # validating  options are off
        for opt in options:
            if options_dict[opt] != 'off':
                raise Exception("Options are not set to off")

        # Creating IO on client side
        mount_obj = redant.es.get_mnt_pts_dict_in_list(self.vol_name)[0]
        self.list_of_procs = []
        redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                           f"{mount_obj['mountpath']}")
        path_dir = f"{mount_obj['mountpath']}/{test_dir}"
        proc = redant.create_deep_dirs_with_files(path_dir,
                                                  1,
                                                  1, 0, 1, 0,
                                                  mount_obj['client'])

        self.list_of_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, mount_obj)
        if not ret:
            raise Exception("IO validation failed")

        # get the bricks for the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        # Bring brick 1 offline
        bricks_to_bring_offline = [bricks_list[0]]
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_to_bring_offline} "
                            "is not offline")

        # Create file under dir test_dir
        if not (redant.
                create_file(path_dir, 'test_file.txt',
                            mount_obj['client'])):
            print("File creation failed")

        # get md5sum for file
        cmd = (f"md5sum {path_dir}/test_file.txt |"
               " awk '{ print $1 }'")

        ret = redant.execute_abstract_op_node(cmd,
                                              mount_obj['client'])
        md5sum = (ret['msg'][0]).rstrip("\n")
        redant.logger.info(f"md5sum: {md5sum}")

        # Bring brick 2 offline
        bricks_to_bring_offline = [bricks_list[1]]
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_to_bring_offline} "
                            "is not offline")
        # Bring 1-st brick online
        bricks_to_bring_online = [bricks_list[0]]
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_to_bring_online)

        # Rename file under test_dir
        if not (redant.
                move_file(mount_obj['client'], f"{path_dir}/test_file.txt",
                          f"{path_dir}/test_file_new.txt")):
            raise Exception("Failed to rename the file")

        # Bring 2-nd brick online
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_to_bring_offline)

        # Mount and unmount mounts
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])

        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        # Enable client side healing
        options = {"metadata-self-heal": "on",
                   "entry-self-heal": "on",
                   "data-self-heal": "on"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])
        # Trigger heal from mount point
        cmd = (f"cd {path_dir} ; find . | xargs getfattr"
               " -d -m . -e hex")

        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain")

        # Get md5sum for file on all nodes and compare with mountpoint
        for brick in bricks_list[0:2]:
            node, brick_path = brick.split(':')
            cmd = (f"md5sum {brick_path}/{test_dir}/test_file_new.txt"
                   " | awk '{ print $1 }'")

            ret = redant.execute_abstract_op_node(cmd, node)
            md5sum_node = (ret['msg'][0]).rstrip("\n")
            redant.logger.info(f"md5sum: {md5sum_node}")

            # Comparing md5sum_node result with mountpoint
            if md5sum != md5sum_node:
                raise Exception('md5sums are not equal on '
                                f'{mount_obj["client"]} and {brick}')
