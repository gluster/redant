"""
Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module related to Glusterd volume status while
    IOs in progress
@runs_on([['replicated', 'distributed-replicated'], ['glusterfs']])
"""
# disruptive;rep

import random
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    # def tearDown(self):
    #     """
    #     tearDown for every test
    #     """
    #     if not self.io_validation_complete:
    #         g.log.info("Wait for IO to complete as IO validation did not "
    #                    "succeed in test method")
    #         ret = wait_for_io_to_complete(self.all_mounts_procs, self.mounts)
    #         if not ret:
    #             raise ExecutionError("IO failed on some of the clients")
    #         g.log.info("IO is successful on all mounts")

    #         # List all files and dirs created
    #         g.log.info("List all files and directories:")
    #         ret = list_all_files_and_dirs_mounts(self.mounts)
    #         if not ret:
    #             raise ExecutionError("Failed to list all files and dirs")
    #         g.log.info("Listing all files and directories is successful")

    #     ret, _, _ = profile_stop(random.choice(self.servers), self.volname)
    #     self.assertEqual(ret, 0, (
    #         "Volume profile failed to stop for volume %s" % self.volname))
    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Create and start the volume
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)

    def run_test(self, redant):
        '''
        Create replica volume then mount the volume, once
        volume mounted successfully on client, start running IOs on
        mount point then run the "gluster volume <volname> profile info"
        command on all clusters randomly.
        Then check that IOs completed successfully or not on mount point.
        Check that files in mount point listing properly or not.
        check the release directory value should be less or equals '4'
        '''

        status_on = "on"
        validate_profiles = ('cluster.eager-lock',
                             'diagnostics.count-fop-hits',
                             'diagnostics.latency-measurement')

        redant.profile_start(self.vol_name,
                             random.choice(self.server_list))

        # for validate_profile in validate_profiles:
        #     out = get_volume_options(
        #         random.choice(self.servers), self.volname,
        #         option=(validate_profile))
        #     self.assertIsNotNone(out, "Volume get failed for volume "
        #                          "%s" % self.volname)
        #     self.assertEqual(out[validate_profile], status_on, "Failed to "
        #                      "match profile information")

        # # Mounting a volume
        # ret = self.mount_volume(self.mounts)
        # self.assertTrue(ret, "Volume mount failed for %s" % self.volname)

        # # run IOs
        # g.log.info("Starting IO on all mounts...")
        # self.all_mounts_procs = []
        # for mount_obj in self.mounts:
        #     g.log.info("Starting IO on %s:%s", mount_obj.client_system,
        #                mount_obj.mountpoint)
        #     cmd = ("/usr/bin/env python %s create_deep_dirs_with_files "
        #            "--dirname-start-num %d "
        #            "--dir-depth 2 "
        #            "--dir-length 15 "
        #            "--max-num-of-dirs 5 "
        #            "--num-of-files 25 %s" % (self.script_upload_path,
        #                                      self.counter,
        #                                      mount_obj.mountpoint))

        #     proc = g.run_async(mount_obj.client_system, cmd,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        #     self.counter = self.counter + 10
        # self.io_validation_complete = False

        # # this command should not get hang while io is in progress
        # # pylint: disable=unused-variable
        # for i in range(20):
        #     ret, _, _ = profile_info(
        #         random.choice(self.servers), self.volname)
        #     self.assertEqual(ret, 0, ("Volume profile info failed on "
        #                               "volume %s" % self.volname))

        # # Validate IO
        # ret = validate_io_procs(self.all_mounts_procs, self.mounts)
        # self.io_validation_complete = True
        # self.assertTrue(ret, "IO failed on some of the clients")

        # # List all files and dirs created
        # ret = list_all_files_and_dirs_mounts(self.mounts)
        # self.assertTrue(ret, "Failed to list all files and dirs")
        # g.log.info("Listing all files and directories is successful")

        # volume_profile_info = "gluster v profile %s info"
        # _, out, _ = g.run(random.choice(self.servers),
        #                   volume_profile_info % self.volname + " | grep"
        #                   "OPENDIR | awk '{print$8}'")
        # self.assertIsNotNone(out, "Failed to get volume %s profile info" %
        #                      self.volname)
        # out.strip().split('\n')
        # for value in out:
        #     self.assertLessEqual(value, '4', "Failed to Validate profile"
        #                          " on volume %s" % self.volname)
