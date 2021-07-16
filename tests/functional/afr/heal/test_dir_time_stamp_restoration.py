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

    # def are_mdata_xattrs_equal(self):
    #     """Check if atime/mtime/ctime in glusterfs.mdata xattr are identical"""
    #     timestamps = []
    #     for brick_path in self.bricks_list:
    #         server, brick = brick_path.split(':')
    #         fattr = get_fattr(server, '%s/%s' % (brick, "dir1"),
    #                           'trusted.glusterfs.mdata')
    #         self.assertIsNotNone(fattr, 'Unable to get mdata xattr')
    #         timestamps.append(fattr)

    #     g.log.debug("mdata list = %s", ''.join(map(str, timestamps)))
    #     return timestamps.count(timestamps[0]) == len(timestamps)

    # def are_stat_timestamps_equal(self):
    #     """Check if atime/mtime/ctime in stat info are identical"""
    #     timestamps = []
    #     for brick_path in self.bricks_list:
    #         server, brick = brick_path.split(':')
    #         stat_data = get_file_stat(server, "%s/dir1" % brick)
    #         ts_string = "{}-{}-{}".format(stat_data['epoch_atime'],
    #                                       stat_data['epoch_mtime'],
    #                                       stat_data['epoch_ctime'])
    #         timestamps.append(ts_string)

    #     g.log.debug("stat list = %s", ''.join(map(str, timestamps)))
    #     return timestamps.count(timestamps[0]) == len(timestamps)

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
        redant.set_volume_options(self.vol_name, option,
                                  self.server_list[0])

        client, m_point = (self.mounts[0].client_system,
                           self.mounts[0].mountpoint)

        # dirpath = '{}/dir1'.format(m_point)
        # ret = mkdir(client, dirpath)
        # self.assertTrue(ret, 'Unable to create a directory from mount point')

        # bricks_to_bring_offline = select_volume_bricks_to_bring_offline(
        #     self.mnode, self.volname)
        # self.assertIsNotNone(bricks_to_bring_offline, "List is empty")
        # ret = bring_bricks_offline(self.volname, bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks {} offline'.
        #                 format(bricks_to_bring_offline))
        # ret = are_bricks_offline(self.mnode, self.volname,
        #                          bricks_to_bring_offline)
        # self.assertTrue(ret, 'Bricks {} are not offline'.
        #                 format(bricks_to_bring_offline))

        # cmd = 'touch {}/file1'.format(dirpath)
        # ret, _, _ = g.run(client, cmd)
        # self.assertEqual(ret, 0, 'Unable to create file from mount point')

        # ret = bring_bricks_online(
        #     self.mnode, self.volname,
        #     bricks_to_bring_offline,
        #     bring_bricks_online_methods=['volume_start_force'])
        # self.assertTrue(ret, 'Failed to bring bricks {} online'.format
        #                 (bricks_to_bring_offline))
        # ret = trigger_heal(self.mnode, self.volname)
        # self.assertTrue(ret, 'Starting heal failed')
        # ret = monitor_heal_completion(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal has not yet completed')

        # if ctime:
        #     ret = self.are_mdata_xattrs_equal()
        #     self.assertTrue(ret, "glusterfs.mdata mismatch for {}"
        #                     .format(dirpath))
        # else:
        #     ret = self.are_stat_timestamps_equal()
        #     self.assertTrue(ret, "stat mismatch for {}".format(dirpath))

        # ret = rmdir(client, dirpath, force=True)
        # self.assertTrue(ret, 'Unable to delete directory from mount point')

    def test_dir_time_stamp_restoration(self):
        """
        Create pending entry self-heal on a replica volume and verify that
        after the heal is complete, the atime, mtime and ctime of the parent
        directory are identical on all bricks of the replica.

        The test is run with features.ctime enabled as well as disabled.
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.bricks_list = get_all_bricks(self.mnode, self.volname)
        self._perform_test(ctime=True)
        self._perform_test(ctime=False)
