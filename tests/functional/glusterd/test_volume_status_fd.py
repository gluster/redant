#  Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

""" Description:
        Test Cases in this module related to Glusterd volume status fd while
        IOs in progress
"""

# nonDisruptive;dist
import random
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        '''
        -> Create volume
        -> Mount the volume on 2 clients
        -> Run I/O's on mountpoint
        -> While I/O's are in progress
        -> Perform gluster volume status fd repeatedly
        -> List all files and dirs listed
        '''

        # Check if the volume is mounted
        redant.get_mounts_stat(self.mountpoint)

        # run IO on mountpoint
        redant.logger.info("Starting IO on all mounts...")
        list_of_procs = redant.run_linux_untar(self.client_list[0],
                                               self.mountpoint)

        # performing  "gluster volume status volname fd" command on
        # all cluster servers randomly while io is in progress,
        # this command should not get hang while io is in progress
        count = 0
        while count < 300:
            cmd = f"gluster volume status {self.vol_name} fd"
            server = random.choice(self.server_list)
            redant.execute_abstract_op_node(cmd, server)
            redant.logger.info(f"Successful in logging volume status"
                               f"fd of volume {self.vol_name}")
            count += 1

        # Get mountpoint list
        mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Validate IO
        ret = redant.validate_io_procs(list_of_procs, mnt_list)
        if not ret:
            raise Exception("IO validation failed")

        # List all files and dirs created
        redant.logger.info("List all files and directories:")
        ret = redant.list_all_files_and_dirs_mounts(mnt_list)
        if not ret:
            raise Exception("Failed to list all files and dirs")
