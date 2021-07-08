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
    TC to check glusterfind delete operation
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class GlusterFindDeleteCLI(DParentTest):

    def terminate(self):
        """
        Delete glusterfind sessions, if they exist
        """

        # Check if glusterfind list contains any sessions
        # If session exists, then delete it
        try:
            ret = self.redant.gfind_list(self.server_list[0], self.vol_name,
                                         self.session, excep=False)
            if ret['error_code'] == 0:
                self.redant.logger.error("Unexpected: Glusterfind list shows"
                                         " existing session")
                self.redant.gfind_delete(self.server_list[0], self.vol_name,
                                         self.session)

            self.redant.logger.info("No session is listed")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Verifying the glusterfind delete command functionality with valid
        and invalid values for the required and optional parameters.

        * Create a volume
        * Create a session on the volume
        * Perform glusterfind list to check if session is created
        * Delete the glusterfind session with the following combinations:
            - Valid values for required parameters
            - Invalid values for required parameters
            - Valid values for optional parameters
            - Invalid values for optional parameters
        * Perform glusterfind list to check if session is deleted

            Required parameters: volname and sessname
            Optional parameters: debug
        """

        self.session = f"test-session-{self.vol_name}"

        # Creating a session for the volume
        redant.gfind_create(self.server_list[0], self.vol_name, self.session)

        # Perform glusterfind list to check if session exists
        redant.gfind_list(self.server_list[0], self.vol_name, self.session)

        # Delete the glusterfind session using the invalid values for optional
        # parameters
        cmd = f"glusterfind delete {self.vol_name} {self.session} --dbug"
        ret = redant.execute_abstract_op_node(cmd, self.server_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: glusterfind session deleted even"
                            " with invalid value for optional parameters")

        # Delete the glusterfind session using the valid values for required
        # and optional parameters
        redant.gfind_delete(self.server_list[0], self.vol_name, self.session,
                            debug=True)

        # Perform glusterfind list to check if the session exists
        ret = redant.gfind_list(self.server_list[0], self.vol_name,
                                self.session, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: glusterfind session was listed")
