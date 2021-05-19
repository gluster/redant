"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Check volume status inode while IO is in progress
"""

# nonDisruptive;rep,dist,arb,disp,dist-rep,dist-arb,dist-disp
import random
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        '''
        Create any type of volume then mount the volume, once
        volume mounted successfully on client, start running IOs on
        mount point then run the "gluster volume status volname inode"
        command on all clusters randomly.
            "gluster volume status volname inode" command should not get
        hang while IOs in progress.
        Then check that IOs completed successfully or not on mount point.
        Check that files in mount point listing properly or not.
        '''

        # Get mountpoint list
        mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Check if the volume is mounted
        redant.get_mounts_stat(mnt_list)

        # run IO on mountpoint
        redant.logger.info("Starting IO on all mounts...")
        list_of_procs = redant.run_linux_untar(self.client_list[0],
                                               self.mountpoint)

        # performing  "gluster volume status volname inode" command on
        # all cluster servers randomly while io is in progress,
        # this command should not get hang while io is in progress
        # pylint: disable=unused-variable
        for i in range(20):
            cmd = (f"gluster --timeout=12000 volume status {self.vol_name}"
                   f" inode")
            server = random.choice(self.server_list)
            redant.execute_abstract_op_node(cmd, server)
            redant.logger.info(f"Successful in logging volume status"
                               f"inode of volume {self.vol_name}")

        # Validate IO
        ret = redant.validate_io_procs(list_of_procs, mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # List all files and dirs created
        redant.logger.info("List all files and directories:")
        ret = redant.list_all_files_and_dirs_mounts(mnt_list)
        if not ret:
            raise Exception("Failed to list all files and dirs")
