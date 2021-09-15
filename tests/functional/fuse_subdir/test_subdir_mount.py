"""
 Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module tests the Fuse sub directory feature
"""

# nonDisruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.nd_parent_test import NdParentTest


class TestFuseSubDirMount(NdParentTest):

    def terminate(self):
        """
        Unmount the subdirs mounted in the TC, if the TC fails midway
        """
        try:
            if self.is_mounted:
                cmd = f"umount {self.mountpoint}"
                self.redant.execute_abstract_op_node(cmd, self.client_list[0],
                                                     False)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1. Create a sub-directory on the mounted volume.
        2. Unmount volume.
        3. Mount sub-directory on client. This should pass.
        """
        self.is_mounted = False

        # Creating a sub directory on mounted volume
        redant.create_dir(self.mountpoint, "d1", self.client_list[0])

        # Unmount volume
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])

        # Mounting sub directory on client.
        volname = f"{self.vol_name}/d1"
        redant.authenticated_mount(volname, self.server_list[0],
                                   self.mountpoint, self.client_list[0])
        self.is_mounted = True

        # Unmount sub directories
        redant.volume_unmount(volname, self.mountpoint,
                              self.client_list[0], check_volds=False)
        self.is_vol_mounted = False
