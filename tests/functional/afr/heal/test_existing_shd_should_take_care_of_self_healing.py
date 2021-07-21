"""
Copyright (C) 2016-2018  Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module tests the self heal daemon process.
@runs_on([['replicated', 'distributed-replicated'],
          ['glusterfs', 'cifs', 'nfs']])
"""
# disruptive;rep
# TODO: nfs, cifs

import time
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def test_existing_glustershd_should_take_care_of_self_healing(self):
        """
        Test Script which verifies that the existing glustershd should take
        care of self healing

        * Create and start the Replicate volume
        * Check the glustershd processes - Note the pids
        * Bring down the One brick ( lets say brick1)  without affecting
          the cluster
        * Create 1000 files on volume
        * bring the brick1 up which was killed in previous steps
        * check the heal info - proactive self healing should start
        * Bring down brick1 again
        * wait for 60 sec and brought up the brick1
        * Check the glustershd processes - pids should be different
        * Monitor the heal till its complete

        """
        # Verfiy glustershd process releases its parent process
        if not redant.is_shd_daemonized(self.server_list)
            raise Exception("Self Heal Daemon process was still"
                            " holding parent process.")

        # # check the self-heal daemon process
        # ret, pids = get_self_heal_daemon_pid(self.server_list)
        # self.assertTrue(ret, ("Either No self heal daemon process found or "
        #                       "more than One self heal daemon process "
        #                       "found : %s" % pids))
        # glustershd_pids = pids

        # # select the bricks to bring offline
        # g.log.info("Selecting bricks to brought offline for volume %s",
        #            self.volname)
        # bricks_to_bring_offline = \
        #     select_volume_bricks_to_bring_offline(self.mnode,
        #                                           self.volname)
        # g.log.info("Brick List to bring offline : %s",
        #            bricks_to_bring_offline)

        # # Bring down the selected bricks
        # g.log.info("Going to bring down the brick process "
        #            "for %s", bricks_to_bring_offline)
        # ret = bring_bricks_offline(self.volname, bricks_to_bring_offline)
        # self.assertTrue(ret, ("Failed to bring down the bricks. Please "
        #                       "check the log file for more details."))
        # g.log.info("Brought down the brick process "
        #            "for %s successfully", bricks_to_bring_offline)

        # # get the bricks which are running
        # g.log.info("getting the brick list which are online")
        # online_bricks = get_online_bricks_list(self.mnode, self.volname)
        # g.log.info("Online Bricks for volume %s : %s",
        #            self.volname, online_bricks)

        # # write 1MB files to the mounts
        # g.log.info("Starting IO on all mounts...")
        # g.log.info("mounts: %s", self.mounts)
        # all_mounts_procs = []
        # cmd = ("for i in `seq 1 1000`; "
        #        "do dd if=/dev/urandom of=%s/file_$i "
        #        "bs=1M count=1; "
        #        "done"
        #        % self.mounts[0].mountpoint)
        # g.log.info(cmd)
        # proc = g.run_async(self.mounts[0].client_system, cmd,
        #                    user=self.mounts[0].user)
        # all_mounts_procs.append(proc)

        # # Validate IO
        # self.assertTrue(
        #     validate_io_procs(all_mounts_procs, self.mounts),
        #     "IO failed on some of the clients"
        # )

        # # check the heal info
        # g.log.info("Get the pending heal info for the volume %s",
        #            self.volname)
        # heal_info = get_heal_info_summary(self.mnode, self.volname)
        # g.log.info("Successfully got heal info for the volume %s",
        #            self.volname)
        # g.log.info("Heal Info for volume %s : %s", self.volname, heal_info)

        # # Bring bricks online
        # g.log.info("Bring bricks: %s online", bricks_to_bring_offline)
        # ret = bring_bricks_online(self.mnode, self.volname,
        #                           bricks_to_bring_offline, 'glusterd_restart')
        # self.assertTrue(ret, ("Failed to bring bricks: %s online"
        #                       % bricks_to_bring_offline))
        # g.log.info("Successfully brought all bricks: %s online",
        #            bricks_to_bring_offline)

        # # Wait for 90 sec to start self healing
        # g.log.info('Waiting for 90 sec to start self healing')
        # time.sleep(90)

        # # check the heal info
        # g.log.info("Get the pending heal info for the volume %s",
        #            self.volname)
        # heal_info_after_brick_online = get_heal_info_summary(self.mnode,
        #                                                      self.volname)
        # g.log.info("Successfully got heal info for the volume %s",
        #            self.volname)
        # g.log.info("Heal Info for volume %s : %s",
        #            self.volname, heal_info_after_brick_online)

        # # check heal pending is decreased
        # flag = False
        # for brick in online_bricks:
        #     if int(heal_info_after_brick_online[brick]['numberOfEntries'])\
        #             < int(heal_info[brick]['numberOfEntries']):
        #         flag = True
        #         break

        # self.assertTrue(flag, "Pro-active self heal is not started")
        # g.log.info("Pro-active self heal is started")

        # # bring down bricks again
        # g.log.info("Going to bring down the brick process "
        #            "for %s", bricks_to_bring_offline)
        # ret = bring_bricks_offline(self.volname, bricks_to_bring_offline)
        # self.assertTrue(ret, ("Failed to bring down the bricks. Please "
        #                       "check the log file for more details."))
        # g.log.info("Brought down the brick process "
        #            "for %s successfully", bricks_to_bring_offline)

        # # wait for 60 sec and brought up the brick again
        # g.log.info('waiting for 60 sec and brought up the brick again')
        # time.sleep(60)
        # g.log.info("Bring bricks: %s online", bricks_to_bring_offline)
        # ret = bring_bricks_online(self.mnode, self.volname,
        #                           bricks_to_bring_offline, 'glusterd_restart')
        # self.assertTrue(ret, ("Failed to bring bricks: %s online"
        #                       % bricks_to_bring_offline))
        # g.log.info("Successfully brought all bricks: %s online",
        #            bricks_to_bring_offline)

        # # Verfiy glustershd process releases its parent process
        # ret = is_shd_daemonized(self.server_list)
        # self.assertTrue(ret, ("Either No self heal daemon process found or "
        #                       "more than One self heal daemon process found"))

        # # check the self-heal daemon process
        # ret, pids = get_self_heal_daemon_pid(self.server_list)
        # self.assertTrue(ret, ("Either No self heal daemon process found or "
        #                       "more than One self heal daemon process "
        #                       "found : %s" % pids))

        # shd_pids_after_bricks_online = pids

        # # compare the glustershd pids
        # self.assertNotEqual(glustershd_pids,
        #                     shd_pids_after_bricks_online,
        #                     ("self heal daemon process are same before and "
        #                      "after bringing up bricks online"))
        # g.log.info("EXPECTED : self heal daemon process are different before "
        #            "and after bringing up bricks online")

        # # wait for heal to complete
        # g.log.info("Monitoring the heal.....")
        # ret = monitor_heal_completion(self.mnode, self.volname)
        # self.assertTrue(ret, ("Heal is not completed on volume %s"
        #                       % self.volname))
        # g.log.info("Heal Completed on volume %s", self.volname)

        # # Check if heal is completed
        # ret = is_heal_complete(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal is not complete')
        # g.log.info('Heal is completed successfully')
