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
    Arbiter Test cases related to
    healing in default configuration of the volume
@runs_on([['arbiter'],
          ['glusterfs', 'nfs', 'cifs']])
"""
class TestArbiterSelfHeal(GlusterBaseClass):

    def terminate(self):
        try:
            if len(self.all_mounts_procs) > 0:
                ret = (self.redant.
                       wait_for_io_to_complete(self.all_mounts_procs,
                                               self.mounts))
                if not ret:
                    raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def test_handling_data_split_brain(self):
        """
        - create IO
        - calculate arequal from mountpoint
        - set volume option 'self-heal-daemon' to value "off"
        - kill data brick1
        - calculate arequal checksum and compare it
        - modify files and directories
        - bring back all bricks processes online
        - kill data brick3
        - modify files and directories
        - calculate arequal from mountpoint
        - bring back all bricks processes online
        - run the find command to trigger heal from mountpoint
        - set volume option 'self-heal-daemon' to value "on"
        - check if heal is completed
        - check for split-brain
        - read files
        - calculate arequal checksum and compare it
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # # Creating files on client side
        # for mount_obj in self.mounts:
        #     g.log.info("Generating data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Create files
        #     g.log.info('Creating files...')
        #     command = ("cd %s ; "
        #                "for i in `seq 1 10` ; "
        #                "do mkdir dir.$i ; "
        #                "for j in `seq 1 5` ; "
        #                "do dd if=/dev/urandom of=dir.$i/file.$j "
        #                "bs=1K count=1 ; "
        #                "done ; "
        #                "dd if=/dev/urandom of=file.$i bs=1k count=1 ; "
        #                "done"
        #                % mount_obj.mountpoint)

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False

        # # Validate IO
        # g.log.info("Wait for IO to complete and validate IO ...")
        # ret = validate_io_procs(self.all_mounts_procs, self.mounts)
        # self.assertTrue(ret, "IO failed on some of the clients")
        # self.io_validation_complete = True
        # g.log.info("IO is successful on all mounts")

        # # Get arequal before getting bricks offline
        # g.log.info('Getting arequal before getting bricks offline...')
        # ret, result_before_offline = collect_mounts_arequal(self.mounts)
        # self.assertTrue(ret, 'Failed to get arequal')
        # g.log.info('Getting arequal before getting bricks offline '
        #            'is successful')

        # # Setting options
        # options = {"self-heal-daemon": "off"}
        # g.log.info('Setting options %s for volume %s',
        #            options, self.volname)
        # ret = set_volume_options(self.mnode, self.volname, options)
        # self.assertTrue(ret, 'Failed to set options %s' % options)
        # g.log.info("Option 'self-heal-daemon' is set to 'off' successfully")

        # # get the bricks for the volume
        # g.log.info("Fetching bricks for the volume: %s", self.volname)
        # bricks_list = get_all_bricks(self.mnode, self.volname)
        # g.log.info("Brick list: %s", bricks_list)

        # # Bring brick 1 offline
        # bricks_to_bring_offline = [bricks_list[0]]
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
        # ret, result_after_offline = collect_mounts_arequal(self.mounts)
        # self.assertTrue(ret, 'Failed to get arequal')
        # g.log.info('Getting arequal after getting bricks offline '
        #            'is successful')

        # # Comparing arequals before getting bricks offline
        # # and after getting bricks offline
        # self.assertEqual(result_before_offline, result_after_offline,
        #                  'Arequals before getting bricks offline '
        #                  'and after getting bricks offline are not equal')
        # g.log.info('Arequals before getting bricks offline '
        #            'and after getting bricks offline are equal')

        # # Modify the data
        # self.all_mounts_procs = []
        # for mount_obj in self.mounts:
        #     g.log.info("Modifying data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Modify files
        #     g.log.info('Modifying files...')
        #     command = ("cd %s ; "
        #                "for i in `seq 1 10` ; "
        #                "do for j in `seq 1 5` ; "
        #                "do dd if=/dev/urandom of=dir.$i/file.$j "
        #                "bs=1M count=1 ; "
        #                "done ; "
        #                "dd if=/dev/urandom of=file.$i bs=1M count=1 ; "
        #                "done"
        #                % mount_obj.mountpoint)

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False

        # # Validate IO
        # g.log.info("Wait for IO to complete and validate IO ...")
        # ret = validate_io_procs(self.all_mounts_procs, self.mounts)
        # self.assertTrue(ret, "IO failed on some of the clients")
        # self.io_validation_complete = True
        # g.log.info("IO is successful on all mounts")

        # # Bring 1-st brick online
        # g.log.info('Bringing bricks %s online...', bricks_to_bring_offline)
        # ret = bring_bricks_online(self.mnode, self.volname,
        #                           bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks %s online' %
        #                 bricks_to_bring_offline)
        # g.log.info('Bringing bricks %s online is successful',
        #            bricks_to_bring_offline)

        # # Bring brick 3rd offline
        # bricks_to_bring_offline = [bricks_list[-1]]
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

        # # Modify the data
        # self.all_mounts_procs = []
        # for mount_obj in self.mounts:
        #     g.log.info("Modifying data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Create files
        #     g.log.info('Modifying files...')
        #     command = ("cd %s ; "
        #                "for i in `seq 1 10` ; "
        #                "do for j in `seq 1 5` ; "
        #                "do dd if=/dev/urandom of=dir.$i/file.$j "
        #                "bs=1M count=1 ; "
        #                "done ; "
        #                "dd if=/dev/urandom of=file.$i bs=1M count=1 ; "
        #                "done"
        #                % mount_obj.mountpoint)

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False

        # # Validate IO
        # g.log.info("Wait for IO to complete and validate IO ...")
        # ret = validate_io_procs(self.all_mounts_procs, self.mounts)
        # self.assertTrue(ret, "IO failed on some of the clients")
        # self.io_validation_complete = True
        # g.log.info("IO is successful on all mounts")

        # # Get arequal before getting bricks online
        # g.log.info('Getting arequal before getting bricks online...')
        # ret, result_before_online = collect_mounts_arequal(self.mounts)
        # self.assertTrue(ret, 'Failed to get arequal')
        # g.log.info('Getting arequal before getting bricks online '
        #            'is successful')

        # # Bring 3rd brick online
        # g.log.info('Bringing bricks %s online...', bricks_to_bring_offline)
        # ret = bring_bricks_online(self.mnode, self.volname,
        #                           bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks %s online' %
        #                 bricks_to_bring_offline)
        # g.log.info('Bringing bricks %s online is successful',
        #            bricks_to_bring_offline)

        # # Mount and unmount mounts
        # ret = self.unmount_volume(self.mounts)
        # self.assertTrue(ret, 'Failed to unmount %s' % self.volname)

        # ret = self.mount_volume(self.mounts)
        # self.assertTrue(ret, 'Unable to mount %s' % self.volname)

        # # Start heal from mount point
        # g.log.info('Starting heal from mount point...')
        # for mount_obj in self.mounts:
        #     g.log.info("Start heal for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     command = "/usr/bin/env python %s read %s" % (
        #         self.script_upload_path,
        #         self.mounts[0].mountpoint)
        #     ret, _, err = g.run(mount_obj.client_system, command)
        #     self.assertFalse(ret, err)
        #     g.log.info("Heal triggered for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        # g.log.info('Heal triggered for all mountpoints')

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

        # # Reading files
        # g.log.info('Reading files...')
        # for mount_obj in self.mounts:
        #     g.log.info("Start reading files for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     command = ('cd %s/ ; '
        #                'for i in `seq 1 10` ; '
        #                'do cat file.$i > /dev/null ; '
        #                'for j in `seq 1 5` ; '
        #                'do cat dir.$i/file.$j > /dev/null ; '
        #                'done ; done'
        #                % mount_obj.mountpoint)
        #     ret, _, err = g.run(mount_obj.client_system, command)
        #     self.assertFalse(ret, err)
        #     g.log.info("Reading files successfully for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        # g.log.info('Reading files successfully for all mountpoints')

        # # Get arequal after getting bricks online
        # g.log.info('Getting arequal after getting bricks online...')
        # ret, result_after_online = collect_mounts_arequal(self.mounts)
        # self.assertTrue(ret, 'Failed to get arequal')
        # g.log.info('Getting arequal after getting bricks online '
        #            'is successful')

        # # Comparing arequals before getting bricks online
        # # and after getting bricks online
        # self.assertEqual(result_before_online, result_after_online,
        #                  'Arequals before getting bricks online '
        #                  'and after getting bricks online are not equal')
        # g.log.info('Arequals before getting bricks online '
        #            'and after getting bricks online are equal')
