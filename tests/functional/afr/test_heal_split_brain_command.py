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
    TC to simulate and validate data, metadata and entry split brain
"""

# disruptive;rep,arb
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestSplitBrain(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Check for RHGS installation
        self.redant.check_gluster_installation(self.server_list, "downstream")

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def _run_cmd_and_validate(self, client, cmd, paths):
        """
        Run `cmd` from `paths` on `client`
        """
        for path in paths:
            self.redant.execute_abstract_op_node(cmd % path, client)

    @staticmethod
    def _transform_gfids(gfids):
        """
        Returns list of `gfids` joined by `-` at required places

        Example of one elemnt:
        Input:   0xd4653ea0289548eb81b35c91ffb73eff
        Returns: d4653ea0-2895-48eb-81b3-5c91ffb73eff
        """
        split_pos = [10, 14, 18, 22]
        rout = []
        for gfid in gfids:
            rout.append('-'.join(
                gfid[start:stop]
                for start, stop in zip([2] + split_pos, split_pos + [None])))
        return rout

    def run_test(self, redant):
        """
        Steps:
        - Create and mount a replicated volume and disable quorum, self-heal
          deamon
        - Create ~10 files from the mount point and simulate data, metadata
          split-brain for 2 files each
        - Create a dir with some files and simulate entry/gfid split brain
        - Validate volume successfully recognizing split-brain
        - Validate a lookup on split-brain files fails with EIO error on mount
        - Validate `heal info` and `heal info split-brain` command shows only
          the files that are in split-brain
        - Validate new files and dir's can be created from the mount
        """
        io_cmd = 'cat /dev/urandom | tr -dc [:space:][:print:] | head -c '
        client, m_point = (self.client_list[0], self.mountpoint)
        arbiter = self.volume_type.find('arb') >= 0

        # Disable self-heal daemon and set `quorum-type` option to `none`
        options = {
            'self-heal-daemon': 'off',
            'cluster.quorum-type': 'none'
        }
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Create required dir's from the mount
        fqpath = f'{m_point}/dir'
        file_io = ('cd %s; for i in {1..6}; do '
                   f'{io_cmd} 2M > file$i; done;')
        file_cmd = 'cd %s; touch file{7..10}'
        redant.execute_abstract_op_node(f"mkdir {fqpath}", client)

        # Create empty files and data files
        for cmd in (file_io, file_cmd):
            self._run_cmd_and_validate(client, cmd, [m_point, fqpath])

        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if all_bricks is None:
            raise Exception('Unable to get list of bricks associated with '
                            'the volume')

        # Data will be appended to the files `file1, file2` resulting in data
        # split brain
        data_split_cmd = ';'.join(io_cmd + '2M >> ' + each_file
                                  for each_file in ('file1', 'file2'))

        # File permissions will be changed for `file4, file5` to result in
        # metadata split brain
        meta_split_cmd = ';'.join('chmod 0555 ' + each_file
                                  for each_file in ('file4', 'file5'))

        # Files will be deleted and created with data to result in data,
        # metadata split brain on files and entry(gfid) split brain on dir
        entry_split_cmd = ';'.join('rm -f ' + each_file + ' && ' + io_cmd
                                   + ' 2M > ' + each_file
                                   for each_file in ('dir/file1', 'dir/file2'))

        # Need to always select arbiter(3rd) brick if volume is arbiter type or
        # any two bricks for replicated volume
        for bricks in zip(all_bricks, all_bricks[1:] + [all_bricks[0]]):

            # Skip iteration if volume type is arbiter and `bricks` doesn't
            # contain arbiter brick
            if arbiter and (all_bricks[-1] not in bricks):
                continue

            # Bring bricks offline
            if not redant.bring_bricks_offline(self.vol_name, list(bricks)):
                raise Exception(f'Unable to bring {bricks} offline')

            # Run cmd to bring files into split brain
            for cmd, msg in ((data_split_cmd, 'data'),
                             (meta_split_cmd, 'meta'), (entry_split_cmd,
                                                        'entry')):
                redant.execute_abstract_op_node(f'cd {m_point}; {cmd}',
                                                client)

            # Bring offline bricks online
            if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                              list(bricks)):
                raise Exception(f'Unable to bring {bricks} online')

            # Confirm if the bricks are online
            if not redant.are_bricks_online(self.vol_name, list(bricks),
                                            self.server_list[0]):
                raise Exception("Bricks are not yet online")

        # Validate volume is in split-brain
        if not redant.is_volume_in_split_brain(self.server_list[0],
                                               self.vol_name):
            raise Exception("Volume should be in split-brain state")

        # Validate `head` lookup on split brain files fails with EIO
        for each_file in ('file1', 'file2', 'file4', 'file5', 'dir/file1',
                          'dir/file2'):
            cmd = f'cd {m_point}; head {each_file}'
            ret = redant.execute_abstract_op_node(cmd, client, False)
            if ret['error_code'] == 0:
                raise Exception(f'Lookup on split-brain file {each_file} '
                                'should have failed')
            if 'Input/output error' not in ret['error_msg']:
                raise Exception(f'File {each_file} should result in EIO'
                                ' error')

        # Validate presence of split-brain files and absence of other files in
        # `heal info` and `heal info split-brain` commands
        cmd = f"gluster v heal {self.vol_name} info"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        ret_info = " ".join(ret['msg'])

        cmd = f"gluster v heal {self.vol_name} info split-brain"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0])
        ret_info_spb = " ".join(ret['msg'])

        # Collect `gfid's` of files in data and metadata split-brain
        common_gfids = []
        host, path = all_bricks[0].split(':')
        for each_file in ('file1', 'file2', 'file4', 'file5', 'dir'):
            fattr = redant.get_fattr(f'{path}/{each_file}', 'trusted.gfid',
                                     host)
            fattr = fattr[1].split('=')[1].strip()
            common_gfids.append(fattr)

        # GFID for files under an entry split brain dir differs from it's peers
        uniq_gfids = []
        for brick in all_bricks[:-1] if arbiter else all_bricks:
            host, path = brick.split(':')
            for each_file in ('dir/file1', 'dir/file2'):
                fattr = redant.get_fattr(f'{path}/{each_file}',
                                         'trusted.gfid', host)
                fattr = fattr[1].split('=')[1].strip()
                uniq_gfids.append(fattr)

        # Transform GFIDs to match against o/p of `heal info` and `split-brain`
        common_gfids[:] = self._transform_gfids(common_gfids)
        uniq_gfids[:] = self._transform_gfids(uniq_gfids)

        # Just enough validation by counting occurences asserting success
        common_files = ['/file1 -', '/file2 -', '/file4', '/file5', '/dir ']
        uniq_files = ['/dir/file1', '/dir/file2']

        # Common files should occur 3 times each in `heal info` and
        # `heal info split-brain` or 2 times for arbiter
        occur = 2 if arbiter else 3
        for each_file, gfid in zip(common_files, common_gfids):

            # Check against `heal info` cmd
            if (ret_info.count(gfid) + ret_info.count(each_file)) \
               != occur:
                raise Exception(f'File {each_file[:6]} with gfid {gfid} '
                                'should exist in `heal info`.')

            # Check against `heal info split-brain` cmd
            if (ret_info_spb.count(gfid)
               + ret_info_spb.count(each_file[:6].strip())) != occur:
                raise Exception(f'File {each_file} with gfid {gfid} should '
                                'exist in `heal info split-brain`.')

        # Entry split files will be listed only in `heal info` cmd
        for index, each_file in enumerate(uniq_files):

            # Collect file and it's associated gfid's
            entries = (uniq_files + uniq_gfids)[index::2]
            count = sum(ret_info.count(entry) for entry in entries)
            if count != occur:
                raise Exception('Not able to find existence of entry split '
                                f'brain file {each_file} in `heal info`')

        # Assert no other file is counted as in split-brain
        for cmd, rout, exp_str in (('heal info', ret_info, 'entries: 7'),
                                   ('heal info split-brain', ret_info_spb,
                                    'split-brain: 5')):
            if rout.count(exp_str) != occur:
                raise Exception(f'Each node should list only {exp_str[-1]}'
                                f' entries in {cmd} command')

        # Validate new files and dir can be created from mount
        fqpath = f'{m_point}/temp'
        redant.execute_abstract_op_node(f"mkdir {fqpath}", client)
        for cmd in (file_io, file_cmd):
            self._run_cmd_and_validate(client, cmd, [fqpath])
