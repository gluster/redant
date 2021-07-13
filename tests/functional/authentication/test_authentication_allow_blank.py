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
    TC to check if setting empty value in auth.allow throws an error
"""

# nonDisruptive;rep,dist-rep,disp,dist-disp
from tests.nd_parent_test import NdParentTest


class TestAuthAllowEmptyString(NdParentTest):

    def run_test(self, redant):
        """
        -Set Authentication allow as empty string for volume
        -Check if glusterd is running
        """
        # Set Authentication to blank string for volume
        option = {"auth.allow": " "}
        ret = redant.set_volume_options(self.vol_name, option,
                                        self.server_list[0], excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Authentication set successfully "
                            f"for Volume with option: {option}")

        # Check if glusterd is running
        ret = redant.is_glusterd_running(self.server_list)
        if ret != 1:
            raise Exception("Glusterd service is not running")
