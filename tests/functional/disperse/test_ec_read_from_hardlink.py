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
    TC to check read from hardlink in case of ec volume
"""

# nonDisruptive;disp,dist-disp
from tests.nd_parent_test import NdParentTest


class TestEcReadFromHardlink(NdParentTest):

    def run_test(self, redant):
        """
        Test steps:
        1. Enable metadata-cache(md-cache) options on the volume
        2. Touch a file and create a hardlink for it
        3. Read data from the hardlink.
        4. Read data from the actual file.
        """
        # Set metadata-cache options as group
        options = {'group': 'metadata-cache'}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        file_name = f"{self.mountpoint}/test1"
        content = "testfile"
        hard_link = f"{self.mountpoint}/test1_hlink"
        cmd = f'echo "{content}" > {file_name}'

        # Creating a file with data
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Creating a hardlink for the file created
        ret = redant.create_link_file(self.client_list[0], file_name,
                                      hard_link)
        if not ret:
            raise Exception("Link file creation failed")

        # Reading from the file as well as the hardlink
        for each in (file_name, hard_link):
            ret = redant.execute_abstract_op_node(f"cat {each}",
                                                  self.client_list[0], False)
            if ret['error_code'] != 0:
                raise Exception(f"Unable to read the {each}")
            if ret['msg'][0].strip() != content:
                raise Exception(f"The content {content} and data in file "
                                f"{each} is not same")
