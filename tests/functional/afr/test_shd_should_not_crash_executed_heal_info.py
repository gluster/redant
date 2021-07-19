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

# disruptive;rep

from tests.d_parent_test import DParentTest

class TestCase(DParentTest):

    def run_test(self, redant):
        """
        - set "entry-self-heal", "metadata-self-heal", "data-self-heal" to off
        - write a few files
        - bring down brick0
        - add IO
        - do a heal info and check for files pending heal on last 2 bricks
        - set "performance.enable-least-priority" to "enable"
        - bring down brick1
        - set the "quorum-type" to "fixed"
        - add IO
        - do a heal info and check for files pending heal on the last brick
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # # Creating files on client side
        # for mount_obj in self.mounts:
        #     g.log.info("Generating data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Create files
        #     g.log.info('Creating files...')
        #     command = ("/usr/bin/env python %s create_files -f 10 "
        #                "--fixed-file-size 1M %s" % (
        #                    self.script_upload_path,
        #                    mount_obj.mountpoint))

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False

        # # Validate IO
        # self.assertTrue(
        #     validate_io_procs(self.all_mounts_procs, self.mounts),
        #     "IO failed on some of the clients"
        # )
        # self.io_validation_complete = True

        # # Bring brick0 offline
        # g.log.info('Bringing bricks %s offline', bricks_list[0])
        # ret = bring_bricks_offline(self.volname, bricks_list[0])
        # self.assertTrue(ret, 'Failed to bring bricks %s offline'
        #                 % bricks_list[0])

        # ret = are_bricks_offline(self.mnode, self.volname,
        #                          [bricks_list[0]])
        # self.assertTrue(ret, 'Bricks %s are not offline'
        #                 % bricks_list[0])
        # g.log.info('Bringing bricks %s offline is successful',
        #            bricks_list[0])

        # # Creating files on client side
        # number_of_files_one_brick_off = '1000'
        # self.all_mounts_procs = []
        # for mount_obj in self.mounts:
        #     g.log.info("Generating data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Create files
        #     g.log.info('Creating files...')
        #     command = ("/usr/bin/env python %s create_files "
        #                "-f %s "
        #                "--fixed-file-size 1k "
        #                "--base-file-name new_file "
        #                "%s"
        #                % (self.script_upload_path,
        #                   number_of_files_one_brick_off,
        #                   mount_obj.mountpoint))

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False

        # # Validate IO
        # self.assertTrue(
        #     validate_io_procs(self.all_mounts_procs, self.mounts),
        #     "IO failed on some of the clients"
        # )
        # self.io_validation_complete = True

        # # Get heal info
        # g.log.info("Getting heal info...")
        # heal_info_data = get_heal_info_summary(self.mnode, self.volname)
        # self.assertIsNotNone(heal_info_data, 'Failed to get heal info.')
        # g.log.info('Success in getting heal info')

        # # Check quantity of file pending heal
        # for brick in bricks_list[1:]:
        #     self.assertEqual(heal_info_data[brick]['numberOfEntries'],
        #                      str(int(number_of_files_one_brick_off)+1),
        #                      'Number of files pending heal is not correct')

        # # Setting options
        # g.log.info('Setting options...')
        # options = {"performance.enable-least-priority": "enable"}
        # ret = set_volume_options(self.mnode, self.volname, options)
        # self.assertTrue(ret, 'Failed to set options %s' % options)
        # g.log.info("Successfully set %s for volume %s",
        #            options, self.volname)

        # # Bring brick1 offline
        # g.log.info('Bringing bricks %s offline', bricks_list[1])
        # ret = bring_bricks_offline(self.volname, bricks_list[1])
        # self.assertTrue(ret, 'Failed to bring bricks %s offline'
        #                 % bricks_list[1])

        # ret = are_bricks_offline(self.mnode, self.volname,
        #                          [bricks_list[1]])
        # self.assertTrue(ret, 'Bricks %s are not offline'
        #                 % bricks_list[1])
        # g.log.info('Bringing bricks %s offline is successful',
        #            bricks_list[1])

        # # Setting options
        # g.log.info('Setting options...')
        # options = {"quorum-type": "fixed"}
        # ret = set_volume_options(self.mnode, self.volname, options)
        # self.assertTrue(ret, 'Failed to set options %s' % options)
        # g.log.info("Successfully set %s for volume %s",
        #            options, self.volname)

        # # Creating files on client side
        # number_of_files_two_brick_off = '100'
        # self.all_mounts_procs = []
        # for mount_obj in self.mounts:
        #     g.log.info("Generating data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Create files
        #     g.log.info('Creating files...')
        #     command = ("/usr/bin/env python %s create_files "
        #                "-f %s "
        #                "--fixed-file-size 1k "
        #                "--base-file-name new_new_file "
        #                "%s"
        #                % (self.script_upload_path,
        #                   number_of_files_two_brick_off,
        #                   mount_obj.mountpoint))

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False

        # # Validate IO
        # self.assertTrue(
        #     validate_io_procs(self.all_mounts_procs, self.mounts),
        #     "IO failed on some of the clients"
        # )
        # self.io_validation_complete = True

        # # Get heal info
        # g.log.info("Getting heal info...")
        # heal_info_data = get_heal_info_summary(self.mnode, self.volname)
        # self.assertIsNotNone(heal_info_data, 'Failed to get heal info.')
        # g.log.info('Success in getting heal info')

        # # Check quantity of file pending heal
        # number_of_files_to_check = str(int(number_of_files_one_brick_off) +
        #                                int(number_of_files_two_brick_off) + 1)
        # self.assertEqual(heal_info_data[bricks_list[-1]]['numberOfEntries'],
        #                  number_of_files_to_check,
        #                  'Number of files pending heal is not correct')
