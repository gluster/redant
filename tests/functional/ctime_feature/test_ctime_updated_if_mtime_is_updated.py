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
    Whenever atime or mtime gets updated ctime too must get updated
"""

# nonDisruptive;dist,rep,dist-rep,disp,dist-disp,arb,dist-arb
from time import sleep
from tests.nd_parent_test import NdParentTest


class TestCtimeGetUpdated(NdParentTest):

    def run_test(self, redant):
        """
        1. test with features.ctime enabled
        2. touch /mnt/file1
        3. stat /mnt/file1
        4. sleep 1;
        5. touch -m -d "2020-01-01 12:00:00" /mnt/file1
        6. stat /mnt/file1
        """
        # Enable features.ctime
        redant.set_volume_options(self.vol_name, {'features.ctime': 'on'},
                                  self.server_list[0])

        # Create a file on the mountpoint
        file_path = f"{self.mountpoint}/file_zyx1"
        create_file_cmd = f"touch {file_path}"
        redant.execute_abstract_op_node(create_file_cmd, self.client_list[0])

        # Get stat of the file
        stat_data = redant.get_file_stat(self.client_list[0], file_path)
        if stat_data is None:
            raise Exception(f"stat on {file_path} failed")

        cmd = f'touch -m -d "2020-01-01 12:00:00" {file_path}'
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        sleep(3)
        stat_data1 = redant.get_file_stat(self.client_list[0], file_path)
        if stat_data1 is None:
            raise Exception(f"stat on {file_path} failed")

        # Check if mtime and ctime are changed
        for key in ('mtime', 'ctime'):
            if stat_data['msg'][key] == stat_data1['msg'][key]:
                raise Exception("Before and after time is same")
