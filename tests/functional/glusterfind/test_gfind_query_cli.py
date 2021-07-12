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
    TC to check glusterfind query operation
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
from tests.d_parent_test import DParentTest


class TestGlusterFindQueryCLI(DParentTest):

    def run_test(self, redant):
        """
        Verifying the glusterfind query command functionality with valid
        and invalid values for the required and optional parameters.

        * Create a volume
        * Perform some I/O from the mount point
        * Perform glusterfind query with the following combinations:
            - Valid values for required parameters
            - Invalid values for required parameters
            - Valid values for optional parameters
            - Invalid values for optional parameters

            Where
            Required parameters: volname and sessname
            Optional parameters: debug
        """
        # Outfile path
        self.outfile = f"/tmp/test-outfile-{self.vol_name}.txt"

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

        # Perform glusterfind query for the volume
        redant.gfind_query(self.server_list[0], self.vol_name, self.outfile,
                           full=True)

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

        # Perform glusterfind query using the invalid values for required
        # parameters
        not_volume = "invalid-volume"
        ret = redant.gfind_query(self.server_list[0], not_volume,
                                 self.outfile, since='none', excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: glusterfind query Successful even"
                            " with invalid values for required parameters")

        # Perform glusterfind query using the invalid values for optional
        # parameters
        invalid_options = [' --dbug', ' --noencod', ' --type n', ' --fll',
                           ' --tagforfullfind', ' --disablepartial',
                           ' --outprefix none', ' --namespc']
        for opt in invalid_options:
            cmd = f"glusterfind query {self.vol_name} {self.outfile} {opt}"
            ret = redant.execute_abstract_op_node(cmd, self.server_list[0],
                                                  False)
            if ret['error_code'] == 0:
                raise Exception("Unexpected: glusterfind query successful"
                                f" for option {opt} which is invalid")
