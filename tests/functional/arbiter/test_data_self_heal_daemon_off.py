"""
Copyright (C) 2020  Red Hat, Inc. <http://www.redhat.com>

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
    Arbiter Test cases related to
    healing in default configuration of the volume

@runs_on([['arbiter', 'distributed-arbiter'], ['glusterfs', 'nfs']])
"""
# disruptive;arb
# TODO: nfs

from time import sleep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Description:
        - set the volume option
        "metadata-self-heal": "off"
        "entry-self-heal": "off"
        "data-self-heal": "off"
        - create IO
        - Get arequal before getting bricks offline
        - set the volume option
        "self-heal-daemon": "off"
        - bring down all bricks processes from selected set
        - Get areeual after getting bricks offline and compare with
        arequal before getting bricks offline
        - modify the data
        - bring bricks online
        - set the volume option
        "self-heal-daemon": "on"
        - check daemons and start healing
        - check if heal is completed
        - check for split-brain
        - add bricks
        - do rebalance
        - create 1k files
        - while creating files - kill bricks and bring bricks online one by one
        in cycle
        - validate IO
        """
        # Setting options
        options = {"metadata-self-heal": "off",
                   "entry-self-heal": "off",
                   "data-self-heal": "off"}
        redant.set_volume_options(self.mnode, self.volname, options)

        # # Creating files on client side
        # cmd = ("/usr/bin/env python %s create_files -f 100"
        #        " --fixed-file-size 1k %s"
        #        % (self.script_upload_path,
        #           self.mounts[0].mountpoint))
        # ret, _, err = g.run(self.mounts[0].client_system, cmd,
        #                     user=self.mounts[0].user)
        # self.assertFalse(ret, 'Failed to create the data for %s: %s'
        #                  % (self.mounts[0].mountpoint, err))
        # g.log.info('Created IO for %s is successfully',
        #            self.mounts[0].mountpoint)

        # # Get arequal before getting bricks offline
        # g.log.info('Getting arequal before getting bricks offline...')
        # ret, arequals = collect_mounts_arequal(self.mounts)
        # self.assertTrue(ret, 'Failed to get arequal')
        # result_before_offline = arequals[0].splitlines()[-1].split(':')[-1]
        # g.log.info('Getting arequal before getting bricks offline '
        #            'is successful')

        # # Setting options
        # g.log.info('Setting options...')
        # options = {"self-heal-daemon": "off"}
        # ret = set_volume_options(self.mnode, self.volname, options)
        # self.assertTrue(ret, 'Failed to set options %s' % options)
        # g.log.info("Option 'self-heal-daemon' is set to 'off' successfully")

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

        # # Get arequal after getting bricks offline
        # g.log.info('Getting arequal after getting bricks offline...')
        # ret, arequals = collect_mounts_arequal(self.mounts)
        # self.assertTrue(ret, 'Failed to get arequal')
        # result_after_offline = arequals[0].splitlines()[-1].split(':')[-1]
        # g.log.info('Getting arequal after getting bricks offline '
        #            'is successful')

        # # Checking arequals before bringing bricks offline
        # # and after bringing bricks offline
        # self.assertEqual(result_before_offline, result_after_offline,
        #                  'Checksums before and '
        #                  'after bringing bricks online are not equal')
        # g.log.info('Checksums before and after bringing bricks online '
        #            'are equal')

        # # Modify the data
        # g.log.info("Modifying data for %s:%s", self.mounts[0].client_system,
        #            self.mounts[0].mountpoint)
        # cmd = ("/usr/bin/env python %s create_files -f 100"
        #        " --fixed-file-size 10k %s"
        #        % (self.script_upload_path,
        #           self.mounts[0].mountpoint))
        # ret, _, err = g.run(self.mounts[0].client_system, cmd,
        #                     user=self.mounts[0].user)
        # self.assertFalse(ret, 'Failed to midify the data for %s: %s'
        #                  % (self.mounts[0].mountpoint, err))
        # g.log.info('Modified IO for %s is successfully',
        #            self.mounts[0].mountpoint)

        # # Bring brick online
        # g.log.info('Bringing bricks %s online...', bricks_to_bring_offline)
        # ret = bring_bricks_online(self.mnode, self.volname,
        #                           bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks %s online' %
        #                 bricks_to_bring_offline)
        # g.log.info('Bringing bricks %s online is successful',
        #            bricks_to_bring_offline)

        # # Setting options
        # g.log.info('Setting options...')
        # options = {"self-heal-daemon": "on"}
        # ret = set_volume_options(self.mnode, self.volname, options)
        # self.assertTrue(ret, 'Failed to set options %s' % options)
        # g.log.info("Option 'self-heal-daemon' is set to 'on' successfully")

        # # Wait for volume processes to be online
        # g.log.info("Wait for volume processes to be online")
        # ret = wait_for_volume_process_to_be_online(self.mnode, self.volname)
        # self.assertTrue(ret, ("Failed to wait for volume %s processes to "
        #                       "be online", self.volname))
        # g.log.info("Successful in waiting for volume %s processes to be "
        #            "online", self.volname)

        # # Verify volume's all process are online
        # g.log.info("Verifying volume's all process are online")
        # ret = verify_all_process_of_volume_are_online(self.mnode, self.volname)
        # self.assertTrue(ret, ("Volume %s : All process are not online"
        #                       % self.volname))
        # g.log.info("Volume %s : All process are online", self.volname)

        # # Wait for self-heal-daemons to be online
        # g.log.info("Waiting for self-heal-daemons to be online")
        # ret = is_shd_daemonized(self.all_servers)
        # self.assertTrue(ret, "Either No self heal daemon process found")
        # g.log.info("All self-heal-daemons are online")

        # # Start healing
        # ret = trigger_heal(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal is not started')
        # g.log.info('Healing is started')

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

        # # Add bricks
        # g.log.info("Start adding bricks to volume...")
        # ret = expand_volume(self.mnode, self.volname, self.servers,
        #                     self.all_servers_info)
        # self.assertTrue(ret, ("Failed to expand the volume %s", self.volname))
        # g.log.info("Expanding volume is successful on "
        #            "volume %s", self.volname)

        # # Do rebalance
        # ret, _, _ = rebalance_start(self.mnode, self.volname)
        # self.assertEqual(ret, 0, 'Failed to start rebalance')
        # g.log.info('Rebalance is started')

        # ret = wait_for_rebalance_to_complete(self.mnode, self.volname)
        # self.assertTrue(ret, 'Rebalance is not completed')
        # g.log.info('Rebalance is completed successfully')

        # # Create 1k files
        # all_mounts_procs = []
        # g.log.info("Modifying data for %s:%s", self.mounts[0].client_system,
        #            self.mounts[0].mountpoint)
        # command = ("/usr/bin/env python %s create_files -f 1000"
        #            " --base-file-name newfile %s"
        #            % (self.script_upload_path, self.mounts[0].mountpoint))

        # proc = g.run_async(self.mounts[0].client_system, command,
        #                    user=self.mounts[0].user)
        # all_mounts_procs.append(proc)

        # # Kill all bricks in cycle
        # bricks_list = get_all_bricks(self.mnode, self.volname)
        # for brick in bricks_list:
        #     # Bring brick offline
        #     g.log.info('Bringing bricks %s offline', brick)
        #     ret = bring_bricks_offline(self.volname, [brick])
        #     self.assertTrue(ret, 'Failed to bring bricks %s offline' % brick)

        #     ret = are_bricks_offline(self.mnode, self.volname, [brick])
        #     self.assertTrue(ret, 'Bricks %s are not offline' % brick)
        #     g.log.info('Bringing bricks %s offline is successful', brick)

        #     # Introducing 30 second sleep when brick is down
        #     g.log.info("Waiting for 30 seconds, with ongoing IO while "
        #                "brick %s is offline", brick)
        #     sleep(30)

        #     # Bring brick online
        #     g.log.info('Bringing bricks %s online...', brick)
        #     ret = bring_bricks_online(self.mnode, self.volname,
        #                               [brick])
        #     self.assertTrue(ret, 'Failed to bring bricks %s online' %
        #                     bricks_to_bring_offline)
        #     g.log.info('Bringing bricks %s online is successful',
        #                brick)

        #     # Wait for volume processes to be online
        #     g.log.info("Wait for volume processes to be online")
        #     ret = wait_for_volume_process_to_be_online(self.mnode,
        #                                                self.volname)
        #     self.assertTrue(ret, ("Failed to wait for volume %s processes to "
        #                           "be online", self.volname))
        #     g.log.info("Successful in waiting for volume %s processes to be "
        #                "online", self.volname)

        #     # Verify volume's all process are online
        #     g.log.info("Verifying volume's all process are online")
        #     ret = verify_all_process_of_volume_are_online(self.mnode,
        #                                                   self.volname)
        #     self.assertTrue(ret, ("Volume %s : All process are not online"
        #                           % self.volname))
        #     g.log.info("Volume %s : All process are online", self.volname)

        #     # Wait for self-heal-daemons to be online
        #     g.log.info("Waiting for self-heal-daemons to be online")
        #     ret = is_shd_daemonized(self.all_servers)
        #     self.assertTrue(ret, "Either No self heal daemon process found or"
        #                          "more than one self heal daemon process"
        #                          "found")
        #     g.log.info("All self-heal-daemons are online")

        # # Validate IO
        # self.assertTrue(
        #     validate_io_procs(all_mounts_procs, self.mounts),
        #     "IO failed on some of the clients")
