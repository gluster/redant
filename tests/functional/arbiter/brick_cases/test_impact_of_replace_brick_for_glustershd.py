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
    Test Cases in this module tests the self heal daemon process.
,dist-arb
"""


# disruptive;arb
# TODO: nfs

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    # @classmethod
    # def setUpClass(cls):
    #     # Calling GlusterBaseClass setUpClass
    #     cls.get_super_method(cls, 'setUpClass')()
    #     cls.glustershd = "/var/lib/glusterd/glustershd/glustershd-server.vol"

    # def setUp(self):
    #     """
    #     setUp method for every test
    #     """

    #     # calling GlusterBaseClass setUp
    #     self.get_super_method(self, 'setUp')()

    #     self.all_mounts_procs = []
    #     self.io_validation_complete = False

    #     # Setup Volume and Mount Volume
    #     g.log.info("Starting to Setup Volume %s", self.volname)
    #     ret = self.setup_volume_and_mount_volume(self.mounts)
    #     if not ret:
    #         raise ExecutionError("Failed to Setup_Volume and Mount_Volume")
    #     g.log.info("Successful in Setup Volume and Mount Volume")

    def run_test(self, redant):

        replaced_bricks = []
        ret, pids = redant.get_self_heal_daemon_pid(self.server_list)
        if not ret:
            print("Either No self heal daemon process found or "
                  "more than One self heal daemon process "
                  f"found : {pids}")
        glustershd_pids = pids
        print(glustershd_pids)
        # get the bricks for the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        print(bricks_list)
        # validate the bricks present in volume info with
        # glustershd server volume file
        if not (redant.
                do_bricks_exist_in_shd_volfile(self.vol_name,
                                               bricks_list,
                                               self.server_list[0])):
            raise Exception("Brick List from volume info is different "
                            "from glustershd server volume file. "
                            "Please check log file for details")
        # # get the subvolumes
        # g.log.info("Starting to get sub-volumes for volume %s", self.volname)
        # subvols_dict = get_subvols(self.mnode, self.volname)
        # num_subvols = len(subvols_dict['volume_subvols'])
        # g.log.info("Number of subvolumes in volume %s:", num_subvols)

        # # replace brick from each sub-vol
        # for i in range(0, num_subvols):
        #     subvol_brick_list = subvols_dict['volume_subvols'][i]
        #     g.log.info("sub-volume %s brick list : %s", i, subvol_brick_list)
        #     brick_to_replace = subvol_brick_list[-1]
        #     new_brick = brick_to_replace + 'new'
        #     g.log.info("Replacing the brick %s for the volume : %s",
        #                brick_to_replace, self.volname)
        #     ret, _, err = replace_brick(self.mnode, self.volname,
        #                                 brick_to_replace, new_brick)
        #     self.assertFalse(ret, err)
        #     g.log.info('Replaced brick %s to %s successfully',
        #                brick_to_replace, new_brick)
        #     replaced_bricks.append(brick_to_replace)

        # # Verify volume's all process are online for 60 sec
        # g.log.info("Verifying volume's all process are online")
        # ret = wait_for_volume_process_to_be_online(self.mnode, self.volname,
        #                                            timeout=60)
        # self.assertTrue(ret, ("Volume %s : All process are not "
        #                       "online", self.volname))
        # g.log.info("Successfully Verified volume %s processes are online",
        #            self.volname)

        # # Verify glustershd process releases its parent process
        # ret = is_shd_daemonized(nodes)
        # self.assertTrue(ret, ("Either No self heal daemon process found or "
        #                       "more than One self heal daemon process found"))

        # # check the self-heal daemon process
        # g.log.info("Starting to get self-heal daemon process on nodes "
        #            "%s", nodes)
        # ret, pids = get_self_heal_daemon_pid(nodes)
        # self.assertTrue(ret, ("Either No self heal daemon process found or"
        #                       " more than One self heal daemon process"
        #                       " found : %s" % pids))
        # g.log.info("Successful in getting Single self heal daemon process"
        #            " on all nodes %s", nodes)
        # glustershd_pids_after_replacement = pids

        # # Compare pids before and after replacing
        # self.assertNotEqual(glustershd_pids,
        #                     glustershd_pids_after_replacement,
        #                     "Self Daemon process is same before and"
        #                     " after replacing bricks")
        # g.log.info("Self Heal Daemon Process is different before and "
        #            "after replacing bricks")

        # # get the bricks for the volume after replacing
        # bricks_list_after_replacing = get_all_bricks(self.mnode, self.volname)
        # g.log.info("Brick List after expanding "
        #            "volume: %s", bricks_list_after_replacing)

        # # validate the bricks present in volume info
        # # with glustershd server volume file after replacing bricks
        # g.log.info("Starting parsing file %s", self.glustershd)
        # ret = do_bricks_exist_in_shd_volfile(self.mnode, self.volname,
        #                                      bricks_list_after_replacing)

        # self.assertTrue(ret, ("Brick List from volume info is different "
        #                       "from glustershd server volume file after "
        #                       "replacing bricks. Please check log file "
        #                       "for details"))
        # g.log.info("Successfully parsed %s file", self.glustershd)
        # g.log.info("Starting to delete replaced brick dir's")

        # # Remove brick directories of the replaced bricks as this is not
        # # handled by tearDown class
        # for bricks in replaced_bricks:
        #     node, brick_path = bricks.split(r':')
        #     cmd = "rm -rf " + brick_path
        #     ret, _, _ = g.run(node, cmd)
        #     if ret:
        #         raise ExecutionError("Failed to delete the brick dir's for"
        #                              " %s and brick %s" % (node, brick_path))
        #     g.log.info("Successfully deleted brick dir's for replaced bricks")