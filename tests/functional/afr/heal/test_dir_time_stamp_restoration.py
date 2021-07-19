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

You should have received a copy of the GNU General Public License along`
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-131 USA.

Description:
    Check if parent directory timestamps are restored after an entry heal.
"""

# disruptive;rep

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def _are_mdata_xattrs_equal(self):
        """
        Check if atime/mtime/ctime in glusterfs.mdata
        xattr are identical
        """
        timestamps = []
        for brick_path in self.bricks_list:
            server, brick = brick_path.split(':')
            fattr = self.redant.get_fattr(f'{brick}/dir1',
                                          'trusted.glusterfs.mdata',
                                          server)
            fattr = fattr[1].split('=')[1].rstrip("\n")
            if fattr is None:
                raise Exception("Unable to get mdata xattr")
            timestamps.append(fattr)

        return timestamps.count(timestamps[0]) == len(timestamps)

    def _are_stat_timestamps_equal(self):
        """
        Check if atime/mtime/ctime in stat info are identical
        """
        timestamps = []
        for brick_path in self.bricks_list:
            server, brick = brick_path.split(':')
            stat_data = (self.redant.
                         get_file_stat(server,
                                       f"{brick}/dir1")['msg'])
            ts_string = (f"{stat_data['st_atime']}-{stat_data['st_mtime']}-"
                         f"{stat_data['st_ctime']}")
            timestamps.append(ts_string)
        return timestamps.count(timestamps[0]) == len(timestamps)

    def _perform_test(self, ctime):
        """
        Testcase steps:
        1. Enable/disable features,ctime based on function argument.
        2. Create a directory on the mount point.
        3. Kill a brick and create a file inside the directory.
        4. Bring the brick online.
        5. Trigger heal and wait for its completion.
        6. Verify that the atime, mtime and ctime of the directory are same on
           all bricks of the replica.
        """
        if ctime:
            option = {'features.ctime': 'on'}
        else:
            option = {'features.ctime': 'off'}
        self.redant.set_volume_options(self.vol_name, option,
                                       self.server_list[0])

        client, m_point = (self.mounts[0]['client'],
                           self.mounts[0]['mountpath'])

        dirpath = f'{m_point}/dir1'
        self.redant.create_dir(m_point, 'dir1', client)

        bricks_to_bring_offline = (self.redant.
                                   select_volume_bricks_to_bring_offline(
                                       self.vol_name,
                                       self.server_list[0]))
        if bricks_to_bring_offline is None:
            raise Exception("List is empty")
        self.redant.bring_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline)
        if not (self.redant.
                are_bricks_offline(self.vol_name, bricks_to_bring_offline,
                                   self.server_list[0])):
            raise Exception(f"Bricks {bricks_to_bring_offline} are"
                            "not offline.")

        cmd = f'touch {dirpath}/file1'
        self.redant.execute_abstract_op_node(cmd, client)

        self.redant.bring_bricks_online(
            self.vol_name, self.server_list,
            bricks_to_bring_offline, True)

        if not (self.redant.
                are_bricks_online(self.vol_name, bricks_to_bring_offline,
                                  self.server_list[0])):
            raise Exception(f"Bricks {bricks_to_bring_offline} are "
                            "not online.")

        if not self.redant.trigger_heal(self.vol_name,
                                        self.server_list[0]):
            raise Exception("Start heal failed")

        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name):
            raise Exception("Heal not yet completed")

        if ctime:
            if not self._are_mdata_xattrs_equal():
                raise Exception(f"glusterfs.mdata mismatch for {dirpath}")
        else:
            if not self._are_stat_timestamps_equal():
                raise Exception(f"stat mismatch for {dirpath}")

        if not self.redant.rmdir(dirpath, client, force=True):
            raise Exception("Failed to delete the directory")

    def run_test(self, redant):
        """
        Create pending entry self-heal on a replica volume and verify that
        after the heal is complete, the atime, mtime and ctime of the parent
        directory are identical on all bricks of the replica.

        The test is run with features.ctime enabled as well as disabled.
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.bricks_list = redant.get_all_bricks(self.vol_name,
                                                 self.server_list[0])
        self._perform_test(ctime=True)
        self._perform_test(ctime=False)
