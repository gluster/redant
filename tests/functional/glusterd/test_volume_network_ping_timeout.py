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
        Test Cases in this module related to Glusterd network ping timeout
        of the volume.
"""

import re
from tests.nd_parent_test import NdParentTest


# nonDisruptive;dist,rep,dist-rep,disp,dist-disp
class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        1) Create Volume
        2) Mount the Volume
        3) Create some files on mount point
        4) calculate the checksum of Mount point
        5) Check the default network ping timeout of the volume.
        6) Change network ping timeout to some other value
        7) calculate checksum again
        8) checksum should be same without remounting the volume.
        """
        options = {"features.trash": "on"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])
        # run IOs
        redant.logger.info("Starting IO on all mounts...")
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for mount in self.mounts:
            redant.logger.info(f"Starting IO on {mount['client']}:"
                               f"{mount['mountpath']}")
            proc = redant.create_files(num_files=1, fix_fil_size="1k",
                                       path=mount['mountpath'],
                                       node=mount['client'],
                                       base_file_name="test_file")
            self.all_mounts_procs.append(proc)

        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO operations failed on some"
                            " or all of the clients")

        # Checksum calculation of mount point before
        # changing network.ping-timeout
        before_checksum = redant.collect_mounts_arequal(self.mounts)

        # List all files and dirs created
        redant.logger.info("List all files and directories:")
        ret = redant.list_all_files_and_dirs_mounts(self.mounts)
        if not ret:
            raise Exception("Failed to list all files and dirs")

        # performing gluster volume get volname all and
        # getting network ping time out value
        volume_options = redant.get_volume_options(self.vol_name,
                                                   node=self.server_list[0])
        ret = False
        if re.search(r'\b42\b', volume_options['network.ping-timeout']):
            ret = True
        if not ret:
            raise Exception("network ping time out value is not correct")

        # Changing network ping time out value to specific volume
        networking_ops = {'network.ping-timeout': '12'}
        ret = redant.set_volume_options(self.vol_name, networking_ops,
                                        self.server_list[0])

        # Checksum calculation of mount point after
        # changing network.ping-timeout
        after_checksum = redant.collect_mounts_arequal(self.mounts)

        # comparing list of checksums of mountpoints before and after
        # network.ping-timeout change
        if before_checksum != after_checksum:
            raise Exception("Checksum not same before and after "
                            "network.ping-timeout change")

        # List all files and dirs created
        redant.logger.info("List all files and directories:")
        ret = redant.list_all_files_and_dirs_mounts(self.mounts)
        if not ret:
            raise Exception("Failed to list all files and dirs")
