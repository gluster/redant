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
    TC to check glusterfind pre operation
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestGlusterFindPreCLI(DParentTest):

    def terminate(self):
        """
        Delete glusterfind session and cleanup outfiles
        """
        try:
            self.redant.gfind_delete(self.server_list[0], self.vol_name,
                                     self.session)
            ret = self.redant.remove_file(self.server_list[0], self.outfile,
                                          True)
            if not ret:
                raise Exception("Failed to remove the outfile "
                                f"{self.outfile}")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Verifying the glusterfind pre command functionality with valid
        and invalid values for the required and optional parameters.

        * Create a volume
        * Create a session on the volume
        * Perform some I/O from the mount point
        * Perform glusterfind pre with the following combinations:
            - Valid values for required parameters
            - Invalid values for required parameters
            - Valid values for optional parameters
            - Invalid values for optional parameters
        * Perform glusterfind post

            Where
            Required parameters: volname, sessname and outfile
            Optional parameters: full, debug, gftype, tagforfullfind,
                                 namespace, noencode, disablepartial,
                                 regenoutfile, outprefix, fieldsep
        """
        self.session = f'test-session-for-post-{self.vol_name}'
        self.outfile = f'/tmp/test-outfile-{self.vol_name}.txt'

        # Creating a session for the volume
        redant.gfind_create(self.server_list[0], self.vol_name, self.session)

        # Perform glusterfind list to check if session exists
        redant.gfind_list(self.server_list[0], self.vol_name, self.session)

        # Starting IO on the mounts
        redant.logger.info("Creating Files on "
                           f"{self.mountpoint}:{self.client_list[0]}")
        cmd = (f"cd {self.mountpoint} ; for i in `seq 1 10` ; "
               "do dd if=/dev/urandom of=file$i bs=1M count=1;done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check if the files exist
        for i in range(1, 11):
            path = f"{self.mountpoint}/file{i}"
            ret = redant.path_exists(self.client_list[0], path)
            if not ret:
                raise Exception("File doesn't exist")

        # Perform glusterfind pre for the session
        redant.gfind_pre(self.server_list[0], self.vol_name, self.session,
                         self.outfile, full=True, noencode=True,
                         debug=True)

        # Check if the outfile exists
        ret = redant.path_exists(self.server_list[0], self.outfile)
        if not ret:
            raise Exception("File doesn't exist")

        # Check if all the files are listed in the outfile
        for i in range(1, 11):
            pattern = f"file{i}"
            ret = redant.check_if_pattern_in_file(self.server_list[0],
                                                  pattern, self.outfile)
            if ret != 0:
                raise Exception("Pattern not found in file")

        # Perform glusterfind post for the session
        redant.gfind_post(self.server_list[0], self.vol_name, self.session)

        # Perform glusterfind pre using the invalid values for required
        # parameters
        not_volume = 'invalid-volume-name'
        not_session = 'invalid-session-name'
        not_outfile = '/tmp/not'
        ret = redant.gfind_pre(self.server_list[0], not_volume, not_session,
                               not_outfile, excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: glusterfind pre Successful "
                            "even with invalid values for required parameters")

        # Perform glusterfind pre using the invalid values for optional
        # parameters
        invalid_options = [' --dbug', ' --noencod', ' --regenout', ' --type n',
                           ' --tagforfullfind', ' --disablepartial', ' --fll'
                           ' --outprefix none', ' --namespc']
        for opt in invalid_options:
            cmd = (f"glusterfind pre {self.vol_name} {self.session} "
                   f"{self.outfile} {opt}")
            ret = redant.execute_abstract_op_node(cmd, self.server_list[0],
                                                  False)
            if ret['error_code'] == 0:
                raise Exception("Unexpected: glusterfind pre successful "
                                f"for option {opt} which is invalid")
