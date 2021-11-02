"""
 Copyright (C) 2017-2020 Red Hat, Inc. <http://www.redhat.com>

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
    TC to simulates gfid split brain on multiple files in a dir and
    resolve them via `bigger-file`, `mtime` and `source-brick` methods
"""

# disruptive;rep,dist-rep,arb,dist-arb
from random import choice
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    @staticmethod
    def _get_two_bricks(subvols, arbiter):
        """
        Yields two bricks from each subvol for dist/pure X arb/repl volumes
        """
        # pylint: disable=stop-iteration-return
        # Get an iterator for py2/3 compatibility
        brick_iter = iter(zip(*subvols))
        prev_brick = next(brick_iter)
        first_brick = prev_brick

        for index, curr_brick in enumerate(brick_iter, 1):
            # `yield` should contain arbiter brick for arbiter type vols
            if not (index == 1 and arbiter):
                yield prev_brick + curr_brick
            prev_brick = curr_brick
        # At the end yield first and last brick from a subvol
        yield prev_brick + first_brick

    def _get_files_in_brick(self, brick_path, dir_path):
        """
        Returns files in format of `dir_path/file_name` from the given brick
        path
        """
        node, path = brick_path.split(':')
        files = self.redant.list_files(node, path, dir_path)
        if files is None:
            raise Exception("Failed to get the list of files")

        files = [(file_name.rsplit('/', 1)[-1]).strip() for file_name in files]
        return [
            each_file for each_file in files
            if each_file in ('file1', 'file2', 'file3')
        ]

    def run_test(self, redant):
        """
        Steps:
        - Create and mount a replicated volume, create a dir and ~10 data files
        - Simulate gfid splits in 9 of the files
        - Resolve each 3 set of files using `bigger-file`, `mtime` and
          `source-bricks` split-brain resoultion methods
        - Trigger and monitor for heal completion
        - Validate all the files are healed and arequal matches for bricks in
          subvols
        """
        io_cmd = 'cat /dev/urandom | tr -dc [:space:][:print:] | head -c '
        arbiter = self.volume_type.find('arb') >= 0

        # Disable self-heal daemon and set `quorum-type` option to `none`
        options = {'self-heal-daemon': 'off', 'cluster.quorum-type': 'none'}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Create required dir and files from the mount
        split_dir = 'gfid_split_dir'
        file_io = (f"cd {self.mountpoint}; for i in {{1..10}}; do "
                   f"{io_cmd} 1M > {split_dir}/file$i; done;")

        redant.create_dir(self.mountpoint, split_dir, self.client_list[0])
        redant.execute_abstract_op_node(file_io, self.client_list[0])

        # `file{4,5,6}` are re-created every time to be used in `bigger-file`
        # resolution method
        cmd = "rm -rf {0}/file{1} && {2} {3}M > {0}/file{1}"
        split_cmds = {
            1:
            ';'.join(cmd.format(split_dir, i, io_cmd, 2) for i in range(1, 7)),
            2:
            ';'.join(cmd.format(split_dir, i, io_cmd, 3) for i in range(4, 7)),
            3: ';'.join(
                cmd.format(split_dir, i, io_cmd, 1) for i in range(4, 10)),
            4: ';'.join(
                cmd.format(split_dir, i, io_cmd, 1) for i in range(7, 10)),
        }

        # Get subvols and simulate entry split brain
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        for index, bricks in enumerate(self._get_two_bricks(subvols, arbiter),
                                       1):
            # Bring down two bricks from each subvol
            if not redant.bring_bricks_offline(self.vol_name, list(bricks)):
                raise Exception(f"Unable to bring {bricks} offline")

            redant.execute_abstract_op_node((f"cd {self.mountpoint}; "
                                             f"{split_cmds[index]}"),
                                            self.client_list[0])

            # Bricks will be brought down only two times in case of arbiter and
            # bringing remaining files into split brain for `latest-mtime` heal
            if arbiter and index == 2:
                redant.execute_abstract_op_node((f"cd {self.mountpoint}; "
                                                 f"{split_cmds[4]}"),
                                                self.client_list[0])

            # Bring offline bricks online
            if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                              list(bricks)):
                raise Exception("Failed to bring bricks online")

            # Confirm if the bricks are online
            if not redant.are_bricks_online(self.vol_name, list(bricks),
                                            self.server_list[0]):
                raise Exception("Bricks are not yet online")

        # Enable self-heal daemon, trigger heal and assert volume is in split
        # brain condition
        if not redant.enable_self_heal_daemon(self.vol_name,
                                              self.server_list[0]):
            raise Exception("Failed to enable self heal daemon")

        if not (redant.wait_for_self_heal_daemons_to_be_online(self.vol_name,
                self.server_list[0])):
            raise Exception('Not all self heal daemons are online')

        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception('Unable to trigger index heal on the volume')

        if not redant.is_volume_in_split_brain(self.server_list[0],
                                               self.vol_name):
            raise Exception("Volume should be in split-brain state")

        # Select source brick and take note of files in source brick
        stop = len(subvols[0]) - 1 if arbiter else len(subvols[0])
        source_bricks = [choice(subvol[0:stop]) for subvol in subvols]
        files = [
            self._get_files_in_brick(path, split_dir) for path in source_bricks
        ]

        # Resolve `file1, file2, file3` gfid split files using `source-brick`
        for index, source_brick in enumerate(source_bricks):
            for each_file in files[index]:
                cmd = (f"gluster volume heal {self.vol_name} split-brain"
                       f" source-brick {source_brick} /{split_dir}/"
                       f"{each_file}")
                redant.execute_abstract_op_node(cmd, self.server_list[0])

        # Resolve `file4, file5, file6` gfid split files using `bigger-file`
        for each_file in ('file4', 'file5', 'file6'):
            cmd = (f"gluster volume heal {self.vol_name} split-brain"
                   f" bigger-file /{split_dir}/{each_file}")
            redant.execute_abstract_op_node(cmd, self.server_list[0])

        # Resolve `file7, file8, file9` gfid split files using `latest-mtime`
        for each_file in ('file7', 'file8', 'file9'):
            cmd = (f"gluster volume heal {self.vol_name} split-brain"
                   f" latest-mtime /{split_dir}/{each_file}")
            redant.execute_abstract_op_node(cmd, self.server_list[0])

        # Unless `shd` is triggered manually/automatically files will still
        # appear in `heal info`
        if not redant.trigger_heal_full(self.vol_name, self.server_list[0]):
            raise Exception('Unable to trigger full heal on the volume')

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("All files in volume should be healed after "
                            "healing files via `source-brick`, `bigger-file`"
                            ", `latest-mtime` methods manually")

        # Validate normal file `file10` and healed files don't differ in
        # subvols via an `arequal`
        for subvol in subvols:
            new_arequal = []
            # Disregard last brick if volume is of arbiter type
            arequal = redant.collect_bricks_arequal(subvol[0:stop])
            for item in arequal:
                item = " ".join(item)
                new_arequal.append(item)

            if len(set(new_arequal)) != 1:
                raise Exception("Mismatch of `arequal` checksum among "
                                f"{subvol[0:stop]} is identified")
