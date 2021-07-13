"""
 Copyright (C) 2020 Red Hat, Inc. <http://www.redhat.com>

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
    Test Glusterfind when brick is down
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp
import traceback
from random import choice
from time import sleep
from tests.d_parent_test import DParentTest


class TestGlusterFindBrickDown(DParentTest):

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

    def _perform_io_and_validate_presence_of_files(self):
        """
        Function to perform the IO and validate the presence of files.
        """
        self.file_limit += 10
        # Starting IO on the mounts
        cmd = (f"cd {self.mountpoint};"
               "touch file{"
               f"{self.file_limit - 10}..{self.file_limit}"
               "}")

        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Gather the list of files from the mount point
        files = self.redant.list_files(self.client_list[0], self.mountpoint)
        if files is None:
            raise Exception("Failed to get the list of files")

        # Check if the files exist
        for filename in files:
            file = filename.rstrip('\n')
            ret = self.redant.path_exists(self.client_list[0],
                                          file)
            if not ret:
                raise Exception(f"Unexpected: File {file} does not exist")

    def _perform_glusterfind_pre_and_validate_outfile(self):
        """
        Function to perform glusterfind pre and validate outfile
        """
        # Perform glusterfind pre for the session
        self.redant.gfind_pre(self.server_list[0], self.vol_name,
                              self.session, self.outfile, full=True,
                              noencode=True, debug=True)

        # Check if the outfile exists
        ret = self.redant.path_exists(self.server_list[0], self.outfile)
        if not ret:
            raise Exception(f"Unexpected: File {self.outfile} does not"
                            " exist")

        # Check if all the files are listed in the outfile
        for i in range(1, self.file_limit+1):
            pattern = f"file{i}"
            ret = self.redant.check_if_pattern_in_file(self.server_list[0],
                                                       pattern, self.outfile)
            if ret != 0:
                raise Exception(f"File file{i} not listed in "
                                f"{self.outfile}")

    def run_test(self, redant):
        """
        Verifying the glusterfind functionality when a brick is down.

        1. Create a volume
        2. Create a session on the volume
        3. Create various files from mount point
        4. Bring down brick process on one of the node
        5. Perform glusterfind pre
        6. Perform glusterfind post
        7. Check the contents of outfile
        """
        self.file_limit = 0
        self.session = f'test-session-{self.vol_name}'
        self.outfile = f"/tmp/test-outfile-{self.vol_name}.txt"

        # Set the changelog rollover-time to 1 second
        option = {'changelog.rollover-time': '1'}
        redant.set_volume_options(self.vol_name, option, self.server_list[0])

        # Creating a session for the volume
        redant.gfind_create(self.server_list[0], self.vol_name, self.session)

        # Perform glusterfind list to check if session exists
        redant.gfind_list(self.server_list[0], self.vol_name, self.session)

        self._perform_io_and_validate_presence_of_files()

        # Wait for changelog to get updated
        sleep(2)

        # Bring one of the brick down.
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if brick_list is None:
            raise Exception("Failed to get bricks list")

        if not redant.bring_bricks_offline(self.vol_name, choice(brick_list)):
            raise Exception("Failed to bring down the brick.")

        self._perform_glusterfind_pre_and_validate_outfile()

        # Perform glusterfind post for the session
        redant.gfind_post(self.server_list[0], self.vol_name, self.session)

        # Bring the brick process up.
        redant.volume_start(self.vol_name, self.server_list[0], force=True)
