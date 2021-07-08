"""
 Copyright (C) 2019  Red Hat, Inc. <http://www.redhat.com>

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY :or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    TC to check glusterfind create operation
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestGlusterFindCreateCLI(DParentTest):

    def terminate(self):
        """
        Delete the sessions in glusterfind
        """

        # Deleting the sessions created
        try:
            if self.sessionList:
                for sess in self.sessionList:
                    self.redant.gfind_delete(self.server_list[0],
                                             self.vol_name, sess)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Verifying the glusterfind create command functionality with valid
        and invalid values for the required and optional parameters.

        * Create a volume
        * Create a session on the volume with the following combinations:
            - Valid values for required parameters
            - Invalid values for required parameters
            - Valid values for optional parameters
            - Invalid values for optional parameters

            Required parameters: volname and sessname
            Optional parameters: debug, force, reset-session-time
        """

        self.sessionList = []

        # Create a session with valid inputs for required parameters
        session1 = 'validsession'
        redant.gfind_create(self.server_list[0], self.vol_name, session1)
        self.sessionList.append(session1)

        # Create a session with invalid inputs for required parameters
        session2 = 'invalidsession'
        ret = redant.gfind_create(self.server_list[0], "invalidVolume",
                                  session2, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Creating session should have failed")

        # Create a session with valid inputs for optional parameters
        session3 = 'validoptsession'
        redant.gfind_create(self.server_list[0], self.vol_name, session3,
                            force=True, resetsesstime=True, debug=True)
        self.sessionList.append(session3)

        # Create a session with invalid inputs for optional parameters
        session4 = 'invalidoptsession'
        cmd = (f"glusterfind create {session4} {self.vol_name} --debg --frce"
               " --resetsessiontime")
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Creating session should have failed")
