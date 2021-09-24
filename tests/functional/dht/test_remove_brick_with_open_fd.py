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
"""

# disruptive;dist-rep,dist-disp,dist-arb,dist
import traceback
from tests.d_parent_test import DParentTest


class TestRemoveBrickWithOpenFD(DParentTest):

    def terminate(self):
        """
        Wait for copy to complete if the TC fails midway
        """
        try:
            if self.is_copy_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.list_of_io_processes, self.mounts)):
                    raise Exception("Failed to completely copy file")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Create volume, start it and mount it.
        2. Open file datafile on mount point and start copying /etc/passwd
           line by line(Make sure that the copy is slow).
        3. Start remove-brick of the subvol to which has datafile is hashed.
        4. Once remove-brick is complete compare the checksum of /etc/passwd
           and datafile.
        """
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        self.is_copy_running = False
        # Open file datafile on mount point and start copying /etc/passwd
        # line by line
        cmd = "cat /etc/passwd | wc -l"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
        out = ret['msg'][0]
        self.list_of_io_processes = []
        cmd = ("cd {}; exec 30<> datafile ;for i in `seq 1 {}`; do "
               "head -n $i /etc/passwd | tail -n 1 >> datafile; sleep 10; done"
               .format(self.mountpoint, out))
        proc = redant.execute_command_async(cmd, self.client_list[0])
        self.list_of_io_processes.append(proc)
        self.is_copy_running = True

        # Start remove-brick of the subvol to which has datafile is hashed
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        hashed_subvol, index = redant.find_hashed_subvol(subvols, '/',
                                                         'datafile')
        if hashed_subvol is None:
            raise Exception('Unable to find hashed subvolume')

        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   subvol_num=index)
        if not ret:
            raise Exception("Failed to remove-brick from volume")

        # Validate if I/O was successful or not.
        ret = redant.validate_io_procs(self.list_of_io_processes, self.mounts)
        if not ret:
            raise Exception("File copy failed on mount point")

        self.is_copy_running = False

        # Compare md5checksum of /etc/passwd and datafile
        md5_of_orginal_file = redant.get_md5sum(self.client_list[0],
                                                '/etc/passwd')
        md5_of_copied_file = (redant.get_md5sum(self.client_list[0],
                              f'{self.mountpoint}/datafile'))
        if md5_of_orginal_file.split()[0] != \
                md5_of_copied_file.split()[0]:
            raise Exception("md5 checksum of original and copied file are"
                            " different")
