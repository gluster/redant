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

 You should have received a copy of the GNU General Public License along`
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    TC to check glusterfind list operation
"""

# disruptive;dist,rep,disp,dist-rep,arb,dist-arb,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestGlusterFindListCLI(DParentTest):

    def terminate(self):
        # Cleanup glusterfind session
        try:
            self.redant.gfind_delete(self.server_list[0], self.vol_name,
                                     self.session)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _check_glusterfind_list_output(self, out):
        """Check if glusterfind list output is proper or not."""
        out = out[2].split()
        if out[0] != self.session:
            raise Exception("Unexpected: Session name not proper in output")

        if out[1] != self.vol_name:
            raise Exception("Unecpected: Volume name not proper in output")

    def run_test(self, redant):
        """
        Verifying the glusterfind list command functionality with valid
        and invalid values for the required and optional parameters.

        * Create a volume
        * Create a session on the volume and call glusterfind list with the
          following combinations:
            - Valid values for optional parameters
            - Invalid values for optional parameters

        NOTE:
          There are no required parameters for glusterfind list command.
        """
        # Creating a glusterfind session
        self.session = "session1"
        redant.gfind_create(self.server_list[0], self.vol_name, self.session)

        # Checking output of glusterfind list
        ret = redant.gfind_list(self.server_list[0], self.vol_name,
                                self.session)

        self._check_glusterfind_list_output(ret['msg'])

        # Check output for glusterfind list with valid and invalid volume name
        for volume, expected_value, validation in ((self.vol_name, 0, 'valid'),
                                                   ("abc", 1, 'invalid')):
            ret = redant.gfind_list(self.server_list[0], volume, excep=False)
            if ret['error_code'] != expected_value:
                raise Exception("Glusterfind list --volume check with "
                                f"{validation} parameter failed")
            if ret['error_code'] == 0:
                self._check_glusterfind_list_output(ret['msg'])

        # Check output for glusterfind list with valid and invalid session name
        for session, expected_value, validation in ((self.session, 0, 'valid'),
                                                    ("abc", 1, 'invalid')):
            ret = redant.gfind_list(self.server_list[0], sessname=session,
                                    excep=False)
            if ret['error_code'] != expected_value:
                raise Exception("Glusterfind list --session check with "
                                f"{validation} parameter failed")
            if ret['error_code'] == 0:
                self._check_glusterfind_list_output(ret['msg'])

        # Check output of glusterind list with debug parameter
        redant.gfind_list(self.server_list[0], debug=True)
