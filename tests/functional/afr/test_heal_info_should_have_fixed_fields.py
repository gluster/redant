"""
Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Verify self-heal Triggers with self heal with heal command
"""

# disruptive;dist-rep
# TODO: nfs, cifs

import traceback
import tests.d_parent_test import DParentTest


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
        - Create IO
        - While IO is creating - bring down a couple of bricks
        - Wait for IO to complete
        - Bring up the down bricks
        - Wait for heal to complete
        - Check for fields 'Brick', 'Status', 'Number of entries' in heal info
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Creating files on client side
        # for mount_obj in self.mounts:
        #     g.log.info("Generating data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Create files
        #     g.log.info('Creating files...')
        #     command = ("/usr/bin/env python %s create_deep_dirs_with_files "
        #                "-d 2 -l 2 -f 50 %s" % (
        #                    self.script_upload_path,
        #                    mount_obj.mountpoint))

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False

        # # Select bricks to bring offline
        # bricks_to_bring_offline_dict = (select_bricks_to_bring_offline(
        #     self.mnode, self.volname))
        # bricks_to_bring_offline = bricks_to_bring_offline_dict['volume_bricks']

        # # Bring brick offline
        # g.log.info('Bringing bricks %s offline...', bricks_to_bring_offline)
        # ret = bring_bricks_offline(self.volname, bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks %s offline' %
        #                 bricks_to_bring_offline)

        # ret = are_bricks_offline(self.mnode, self.volname,
        #                          bricks_to_bring_offline)
        # self.assertTrue(ret, 'Bricks %s are not offline'
        #                 % bricks_to_bring_offline)
        # g.log.info('Bringing bricks %s offline is successful',
        #            bricks_to_bring_offline)

        # # Validate IO
        # self.assertTrue(
        #     validate_io_procs(self.all_mounts_procs, self.mounts),
        #     "IO failed on some of the clients"
        # )
        # self.io_validation_complete = True

        # # Bring brick online
        # g.log.info('Bringing bricks %s online...', bricks_to_bring_offline)
        # ret = bring_bricks_online(self.mnode, self.volname,
        #                           bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks %s online' %
        #                 bricks_to_bring_offline)
        # g.log.info('Bringing bricks %s online is successful',
        #            bricks_to_bring_offline)

        # # Monitor heal completion
        # ret = monitor_heal_completion(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal has not yet completed')

        # # Check if heal is completed
        # ret = is_heal_complete(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal is not complete')
        # g.log.info('Heal is completed successfully')

        # # Check for split-brain
        # ret = is_volume_in_split_brain(self.mnode, self.volname)
        # self.assertFalse(ret, 'Volume is in split-brain state')
        # g.log.info('Volume is not in split-brain state')

        # # Get heal info
        # g.log.info('Getting heal info...')
        # heal_info_dicts = get_heal_info_summary(self.mnode, self.volname)
        # self.assertFalse(ret, 'Failed to get heal info')
        # g.log.info(heal_info_dicts)

        # bricks_list = get_all_bricks(self.mnode, self.volname)
        # self.assertIsNotNone(bricks_list, 'Brick list is None')

        # # Check all fields in heal info dict
        # g.log.info('Checking for all the fields in heal info...')
        # for brick in bricks_list:
        #     g.log.info('Checking fields for %s', brick)
        #     self.assertEqual(heal_info_dicts[brick]['status'], 'Connected',
        #                      'Status is not Connected for brick %s' % brick)
        #     self.assertEqual(heal_info_dicts[brick]['numberOfEntries'], '0',
        #                      'numberOfEntries is not 0 for brick %s' % brick)

        # g.log.info('Successfully checked for all the fields in heal info')
