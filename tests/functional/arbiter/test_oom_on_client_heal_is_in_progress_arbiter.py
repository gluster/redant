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
    This test case deals with Arbiter self-heal tests.

from glusto.core import Glusto as g

from glustolibs.gluster.gluster_base_class import (GlusterBaseClass, runs_on)
from glustolibs.gluster.exceptions import ExecutionError
from glustolibs.gluster.brick_libs import (bring_bricks_offline,
                                           bring_bricks_online,
                                           are_bricks_offline,
                                           get_all_bricks)
from glustolibs.io.utils import (validate_io_procs,
                                 list_all_files_and_dirs_mounts,
                                 wait_for_io_to_complete)
from glustolibs.gluster.lib_utils import list_files
from glustolibs.misc.misc_libs import upload_scripts


@runs_on([['arbiter'],
          ['glusterfs', 'nfs', 'cifs']])

"""

# disruptive;arb
# TODO: add nfs and cifs

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        - Create a 1x(2+1) arbiter replicate volume
        - Create IO
        - Bring down the 1-st data brick while creating IO
        - Bring up the 1-st data brick after creating and checking IO
        - Bring down the 3-d arbiter brick
        - Bring up the 3-d arbiter brick
        - Check there no any oom by listing the files from mountpoint
        """

        # Creating IO on client side
        # for mount_obj in self.mounts:
        #     g.log.info("Generating data for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     # Create files
        #     g.log.info('Creating files...')
        #     command = ("/usr/bin/env python %s create_files "
        #                "-f 1000 "
        #                "--fixed-file-size 10k "
        #                "%s" % (
        #                    self.script_upload_path,
        #                    mount_obj.mountpoint))

        #     proc = g.run_async(mount_obj.client_system, command,
        #                        user=mount_obj.user)
        #     self.all_mounts_procs.append(proc)
        # self.io_validation_complete = False
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.list_of_procs = []
        for mount_obj in self.mnt_list:
            redant.logger.info(f"Starting IO on {mount_obj['client']}:"
                               f"{mount_obj['mountpath']}")
            proc = redant.create_files(num_files=1000,
                                       fix_fil_size="10k",
                                       path=mount_obj['mountpath'],
                                       node=mount_obj['client'])
            self.list_of_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, self.mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # get the bricks for the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        # Bring brick 1 offline
        bricks_to_bring_offline = [bricks_list[0]]
        redant.bring_bricks_offline(self.vol_name,
                                    bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            print(f"Bricks {bricks_to_bring_offline} are not offline")

        # # Bring 1-st brick online
        # g.log.info('Bringing bricks %s online...', bricks_to_bring_offline)
        # ret = bring_bricks_online(self.mnode, self.volname,
        #                           bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks %s online'
        #                 % bricks_to_bring_offline)
        # g.log.info('Bringing bricks %s online is successful',
        #            bricks_to_bring_offline)

        # # Bring brick 3 offline
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

        # # Bring brick 3 online
        # g.log.info('Bringing bricks %s online...', bricks_to_bring_offline)
        # ret = bring_bricks_online(self.mnode, self.volname,
        #                           bricks_to_bring_offline)
        # self.assertTrue(ret, 'Failed to bring bricks %s online'
        #                 % bricks_to_bring_offline)
        # g.log.info('Bringing bricks %s online is successful',
        #            bricks_to_bring_offline)

        # # Get file list from mountpoint
        # g.log.info('Getting file list from mountpoints...')
        # for mount_obj in self.mounts:
        #     g.log.info("Getting file list for %s:%s",
        #                mount_obj.client_system, mount_obj.mountpoint)
        #     g.log.info('Getting file list...')
        #     file_list = list_files(mount_obj.client_system,
        #                            mount_obj.mountpoint)
        #     self.assertIsNotNone(file_list)
        # g.log.info('Getting file list from mountpoints finished successfully')
