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

# disruptive;dist-rep,dist-arb,dist-disp,dist
from time import sleep
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestSparseFileCreationAndDeletion(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 5
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _create_two_sparse_files(self):
        """Create 2 sparse files from /dev/zero and /dev/null"""

        # Create a tuple to hold both the file names
        self.sparse_file_tuple = (
            f"{self.mountpoint}/sparse_file_zero",
            f"{self.mountpoint}/sparse_file_null")

        # Create 2 spares file where one is created from /dev/zero and
        # another is created from /dev/null
        for filename, io_file in ((self.sparse_file_tuple[0], "/dev/zero"),
                                  (self.sparse_file_tuple[1], "/dev/null")):
            cmd = (f"dd if={io_file} of={filename} bs=1M seek=5120 count=1000")
            self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _check_du_and_ls_of_sparse_file(self):
        """Check du and ls -lks on spare files"""

        for filename in self.sparse_file_tuple:

            # Fetch output of ls -lks for the sparse file
            cmd = f"ls -lks {filename}"
            ret = self.redant.execute_abstract_op_node(cmd,
                                                       self.client_list[0])
            ls_value = ret['msg'][0].split(" ")[5]

            # Fetch output of du for the sparse file
            cmd = f"du --block-size=1 {filename}"
            ret = self.redant.execute_abstract_op_node(cmd,
                                                       self.client_list[0])
            du_value = ret['msg'][0].split("\t")[0]

            # Compare du and ls -lks value
            if int(ls_value) == int(du_value):
                raise Exception("Unexpected: Sparse file size coming up same "
                                "for du and ls -lks")

    def _delete_two_sparse_files(self):
        """Delete sparse files"""

        for filename in self.sparse_file_tuple:
            cmd = f"rm -rf {filename}"
            self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def run_test(self, redant):
        """
        Test case:
        1. Create volume with 5 sub-volumes, start and mount it.
        2. Check df -h for available size.
        3. Create 2 sparse file one from /dev/null and one from /dev/zero.
        4. Find out size of files and compare them through du and ls.
           (They shouldn't match.)
        5. Check df -h for available size.(It should be less than step 2.)
        6. Remove the files using rm -rf.
        """
        # Check df -h for avaliable size
        available_space_at_start = (redant.get_size_of_mountpoint(
                                    self.mountpoint, self.client_list[0]))
        if not available_space_at_start:
            raise Exception("Failed to get available space on mount point")

        # Create 2 sparse file one from /dev/null and one from /dev/zero
        self._create_two_sparse_files()

        # Find out size of files and compare them through du and ls
        # (They shouldn't match)
        self._check_du_and_ls_of_sparse_file()

        # Check df -h for avaliable size(It should be less than step 2)
        available_space_now = (redant.get_size_of_mountpoint(
                               self.mountpoint, self.client_list[0]))
        if not available_space_now:
            raise Exception("Failed to get avaliable space on mount point")

        ret = (int(available_space_at_start) > int(available_space_now))
        if not ret:
            raise Exception("Available space at start less than "
                            "available space now")

        # Remove the files using rm -rf
        self._delete_two_sparse_files()

        # Sleep for 180 seconds for the meta data in .glusterfs directory
        # to be removed
        sleep(180)

        # Check df -h after removing sparse files
        available_space_now = (redant.get_size_of_mountpoint(
                               self.mountpoint, self.client_list[0]))

        ret = int(available_space_at_start) - int(available_space_now) < 1500
        if not ret:
            raise Exception("Available space at start and available space now"
                            " is not equal")
