"""
 Copyright (C) 2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check glusterfind with --full, --type option
"""

# disruptive;dist,rep,dist-rep,disp,dist-disp,arb,dist-arb
import traceback
from tests.d_parent_test import DParentTest


class TestGlusterfindTypeOption(DParentTest):

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

    def _check_contents_of_outfile(self, gftype):
        """Check contents of outfile created by query and pre"""
        if gftype == 'f':
            content = self.list_of_files
        elif gftype == 'd':
            content = self.list_of_dirs
        else:
            content = self.list_of_files + self.list_of_dirs

        # Check if outfile is created or not
        ret = self.redant.path_exists(self.server_list[0], self.outfile)
        if not ret:
            raise Exception(f"Unexpected: File {self.outfile} does not exist")

        for value in content:
            ret = self.redant.check_if_pattern_in_file(self.server_list[0],
                                                       value, self.outfile)
            if ret != 0:
                raise Exception(f"Entry for '{value}' not listed in "
                                f"{self.outfile}")

    def run_test(self, redant):
        """
        Verifying the glusterfind --full functionality with --type f,
        --type f and --type both

        * Create a volume
        * Create a session on the volume
        * Create various files on mount point
        * Create various directories on point
        * Perform glusterfind pre with --full --type f --regenerate-outfile
        * Check the contents of outfile
        * Perform glusterfind pre with --full --type d --regenerate-outfile
        * Check the contents of outfile
        * Perform glusterfind pre with --full --type both --regenerate-outfile
        * Check the contents of outfile
        * Perform glusterfind query with --full --type f
        * Check the contents of outfile
        * Perform glusterfind query with --full --type d
        * Check the contents of outfile
        * Perform glusterfind query with --full --type both
        * Check the contents of outfile
        """
        self.session = f'test-session-for-post-{self.vol_name}'
        self.outfile = f'/tmp/test-outfile-{self.vol_name}.txt'

        # Create some files and directories from the mount point
        cmd = (f"cd {self.mountpoint}; mkdir dir;mkdir .hiddendir;touch file;"
               "touch .hiddenfile;mknod blockfile b 1 5;mknod charfile b 1 5;"
               "mkfifo pipefile;touch fileforhardlink;touch fileforsoftlink;"
               "ln fileforhardlink hardlinkfile;ln -s fileforsoftlink "
               "softlinkfile")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create list of files and dir to be used for checking
        self.list_of_files = ['file', '.hiddenfile', 'blockfile', 'charfile',
                              'pipefile', 'fileforhardlink', 'fileforsoftlink',
                              'hardlinkfile', 'softlinkfile']
        self.list_of_dirs = ['dir', '.hiddendir']

        # Creating a session for the volume
        redant.gfind_create(self.server_list[0], self.vol_name, self.session)

        # Perform glusterfind list to check if session exists
        redant.gfind_list(self.server_list[0], self.vol_name, self.session)

        # Perform glusterfind full pre for the session with --type option
        for gftype in ('f', 'd', 'both'):
            redant.gfind_pre(self.server_list[0], self.vol_name, self.session,
                             self.outfile, full=True, gftype=gftype,
                             regenoutfile=True)

            # Check the contents of the outfile
            self._check_contents_of_outfile(gftype)

        # Perform glusterfind full query with the --type option
        for gftype in ('f', 'd', 'both'):
            redant.gfind_query(self.server_list[0], self.vol_name,
                               self.outfile, full=True, gftype=gftype)

            # Check the contents of the outfile
            self._check_contents_of_outfile(gftype)
