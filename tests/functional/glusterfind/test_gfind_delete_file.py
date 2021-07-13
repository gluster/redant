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
    TC to check glusterfind functionality with deleting of files
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestGlusterFindDeletes(DParentTest):

    def terminate(self):
        """
        Delete the glusterfind session and remove the outfiles created during
        the test
        """
        try:
            self.redant.gfind_delete(self.server_list[0], self.vol_name,
                                     self.session)
            for file in self.outfiles:
                ret = self.redant.remove_file(self.server_list[0], file, True)
                if not ret:
                    raise Exception(f"Failed to remove the outfile {file}")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Verifying the glusterfind functionality with deletion of files.

        * Create a volume
        * Create a session on the volume
        * Create various files from mount point
        * Perform glusterfind pre
        * Perform glusterfind post
        * Check the contents of outfile
        * Delete the files created from mount point
        * Perform glusterfind pre
        * Perform glusterfind post
        * Check the contents of outfile
          Files deleted must be listed
        """

        self.session = 'test-session-%s' % self.vol_name
        self.outfiles = [f"/tmp/test-outfile-{self.vol_name}-{i}.txt"
                         for i in range(0, 2)]

        # Set the changelog rollover-time to 1 second
        option = {'changelog.rollover-time': '1'}
        redant.set_volume_options(self.vol_name, option, self.server_list[0])

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
                         self.outfiles[0], full=True, noencode=True,
                         debug=True)

        # Check if the outfile exists
        ret = redant.path_exists(self.server_list[0], self.outfiles[0])
        if not ret:
            raise Exception("File doesn't exist")

        # Check if all the files are listed in the outfile
        for i in range(1, 11):
            pattern = f"file{i}"
            ret = redant.check_if_pattern_in_file(self.server_list[0],
                                                  pattern, self.outfiles[0])
            if ret != 0:
                raise Exception("Pattern not found in file")

        # Perform glusterfind post for the session
        redant.gfind_post(self.server_list[0], self.vol_name, self.session)

        # Delete the files created from mount point
        for i in range(1, 11):
            path = f"{self.mountpoint}/file{i}"
            ret = redant.remove_file(self.client_list[0], path)
            if not ret:
                raise Exception("Failed to delete file")

        # Check if the files deleted exist from mount point
        for i in range(1, 11):
            path = f"{self.mountpoint}/file{i}"
            ret = redant.path_exists(self.client_list[0], path)
            if ret:
                raise Exception("Unexpected: File still exist")

        # Wait for changelog to be updated
        sleep(2)

        # Perform glusterfind pre for the session
        redant.gfind_pre(self.server_list[0], self.vol_name, self.session,
                         self.outfiles[1], debug=True)

        # Check if the outfile exists
        ret = redant.path_exists(self.server_list[0], self.outfiles[1])
        if not ret:
            raise Exception("Path doesn't exist")

        # Check if all the files are listed in the outfile
        for i in range(1, 11):
            pattern = f"DELETE file{i}"
            ret = redant.check_if_pattern_in_file(self.server_list[0],
                                                  pattern, self.outfiles[1])
            if ret != 0:
                raise Exception("Pattern not found in file")
