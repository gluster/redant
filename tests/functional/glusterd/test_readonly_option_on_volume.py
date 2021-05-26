"""
Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>

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
    To validate read only option on mount.
"""


from tests.nd_parent_test import NdParentTest

# nonDisruptive;dist,rep,dist-rep,disp,dist-disp

class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        Test steps:
        1. Create a volume
        2. Mount the volume
        3. set 'read-only on' on the volume
        4. perform some I/O's on mount point
        5. set 'read-only off' on the volume
        6. perform some I/O's on mount point
        """
        error_msg = "Read-only file system"

        # Setting Read-only on volume
        redant.set_volume_options(self.vol_name, {'read-only': 'on'},
                                  self.server_list[0])

        # run IO
        ret = redant.create_dir(self.mountpoint, "temp", self.client_list[0],
                                False)
        if error_msg in ret['error_msg'] and ret['error_code'] == 1:
            redant.logger.info("Readonly file system. Hence IO will fail.")
        else:
            raise Exception("IO succeeded in readonly file system.")

        # Setting read only off in volume options.
        redant.set_volume_options(self.vol_name, {'read-only': 'off'},
                                  self.server_list[0])

        # run IO
        ret = redant.create_dir(self.mountpoint, "temp", self.client_list[0],
                                False)
        if not ret['error_code'] == 0:
            raise Exception("IO falied in a read/write file system.")
