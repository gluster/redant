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
    Arbiter Test cases related to GFID self heal
@runs_on([['arbiter', 'distributed-arbiter'], ['glusterfs']])
"""
# disruptive;arb

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test GFID self heal
        Description:
        - Creating directory test_compilation
        - Write Deep directories and files
        - Get arequal before getting bricks offline
        - Select bricks to bring offline
        - Bring brick offline
        - Delete directory on mountpoint where data is writte
        - Create the same directory and write same data
        - Bring bricks online
        - Wait for volume processes to be online
        - Verify volume's all process are online
        - Monitor heal completion
        - Check for split-brain
        - Get arequal after getting bricks online
        """
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []

        # Creating directory test_compilation
        redant.create_dir(self.mountpoint, 'test_gfid_self_heal',
                          self.client_list[0])

        # Write Deep directories and files
        count = 1
        for mount_obj in self.mounts:
            proc = (redant.
                    create_deep_dirs_with_files(f'{mount_obj["mountpath"]}/dir1',
                                                count, 2, 10, 5, 5,
                                                mount_obj['client']))
            self.all_mounts_procs.append(proc)
            count += 10

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Get arequal before getting bricks offline
        result_before_offline = redant.collect_mounts_arequal(self.mounts)
        if result_before_offline is None:
            raise Exception('Failed to get arequal')

        # Select bricks to bring offline
        bricks_to_bring_offline = (redant.
                                   select_volume_bricks_to_bring_offline(
                                       self.vol_name, self.server_list[0]))
        if bricks_to_bring_offline is None:
            raise Exception("Failed to select bricks from volume")
        print(bricks_to_bring_offline)

        # Bring brick offline
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f'Bricks {bricks_to_bring_offline} '
                            'are not offline')

        # # Delete directory on mountpoint where data is written
        # cmd = ('rm -rf -v %s/test_gfid_self_heal' % self.mounts[0].mountpoint)
        # ret, _, _ = g.run(self.mounts[0].client_system, cmd)
        # self.assertEqual(ret, 0, "Failed to delete directory")
        # g.log.info("Directory deleted successfully for %s", self.mounts[0])

        # # Create the same directory and write same data
        # ret = mkdir(self.mounts[0].client_system, "{}/test_gfid_self_heal"
        #             .format(self.mounts[0].mountpoint))
        # self.assertTrue(ret, "Failed to create directory")
        # g.log.info("Directory 'test_gfid_self_heal' on %s created "
        #            "successfully", self.mounts[0])

        # # Write the same files again
        # count = 1
        # for mount_obj in self.mounts:
        #     cmd = ("/usr/bin/env python %s create_deep_dirs_with_files "
        #            "--dirname-start-num %d --dir-depth 2 "
        #            "--dir-length 10 --max-num-of-dirs 5 "
        #            "--num-of-files 5 %s/dir1" % (
        #                self.script_upload_path, count,
        #                mount_obj.mountpoint))
        #     ret, _, _ = g.run(self.mounts[0].client_system, cmd)
        #     self.assertEqual(ret, 0, "Failed to create files on mountpoint")
        #     g.log.info("Successfully created files on mountpoint")
        #     count += 10

        # # Bring bricks online
        # ret = bring_bricks_online(
        #     self.mnode, self.volname,
        #     bricks_to_bring_offline,
        #     bring_bricks_online_methods=['volume_start_force'])
        # self.assertTrue(ret, 'Failed to bring bricks {} online'.format
        #                 (bricks_to_bring_offline))
        # g.log.info('Bringing bricks %s online is successful',
        #            bricks_to_bring_offline)

        # # Wait for volume processes to be online
        # ret = wait_for_volume_process_to_be_online(self.mnode, self.volname)
        # self.assertTrue(ret, ("Failed to wait for volume {} processes to "
        #                       "be online".format(self.volname)))
        # g.log.info("Successful in waiting for volume %s processes to be "
        #            "online", self.volname)

        # # Verify volume's all process are online
        # ret = verify_all_process_of_volume_are_online(self.mnode, self.volname)
        # self.assertTrue(ret, ("Volume {} : All process are not online".format
        #                       (self.volname)))
        # g.log.info("Volume %s : All process are online", self.volname)

        # # Monitor heal completion
        # ret = monitor_heal_completion(self.mnode, self.volname)
        # self.assertTrue(ret, 'Heal has not yet completed')

        # # Check for split-brain
        # ret = is_volume_in_split_brain(self.mnode, self.volname)
        # self.assertFalse(ret, 'Volume is in split-brain state')
        # g.log.info('Volume is not in split-brain state')

        # # Get arequal after getting bricks online
        # ret, result_after_online = collect_mounts_arequal(self.mounts)
        # self.assertTrue(ret, 'Failed to get arequal')
        # g.log.info('Arequal after getting bricks online '
        #            'is %s', result_after_online)
