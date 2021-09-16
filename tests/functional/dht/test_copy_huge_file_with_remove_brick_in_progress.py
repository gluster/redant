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
    TC to check checksum mismatch if huge file is copied while remove-brick
    in progress
"""

# disruptive;dist-rep,dist-arb,dist-disp,dist
import traceback
from tests.d_parent_test import DParentTest


class TestCopyHugeFileWithRemoveBrickInProgress(DParentTest):

    def terminate(self):
        """
        Wait for copy to complete if the TC fails midway
        """
        try:
            _rc = False
            if self.cp_running:
                if not (self.redant.wait_for_io_to_complete(self.io_proc,
                        self.mounts)):
                    _rc = True

            if self.file_created:
                cmd = "rm -rf /mnt/huge_file.txt"
                self.redant.execute_abstract_op_node(cmd, self.client_list[0])

            if _rc:
                raise Exception("Failed to completely copy file")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create files and dirs on the mount point.
        3. Start remove-brick and copy huge file when remove-brick is
           in progress.
        4. Commit remove-brick and check checksum of orginal and copied file.
        """
        self.cp_running = False
        self.file_created = False

        # Create a directory with some files inside
        cmd = (f"cd {self.mountpoint}; for i in {{1..10}}; do mkdir dir$i; "
               "for j in {1..5}; do dd if=/dev/urandom of=dir$i/file$j bs=1M"
               " count=1; done; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create a huge file under /mnt dir
        redant.execute_abstract_op_node("fallocate -l 5G /mnt/huge_file.txt",
                                        self.client_list[0])
        self.file_created = True

        # Copy a huge file when remove-brick is in progress
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        cmd = f"sleep 30; cd {self.mountpoint}; cp ../huge_file.txt ."
        self.io_proc = redant.execute_command_async(cmd, self.client_list[0])
        self.cp_running = True

        # Start remove-brick on volume and wait for it to complete
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   rebal_timeout=1000)
        if not ret:
            raise Exception("Failed to remove-brick from volume")

        # Validate if copy was successful or not
        ret = redant.validate_io_procs(self.io_proc, self.mounts)
        if not ret:
            raise Exception("File copy failed on mount point")
        self.cp_running = False

        # Check checksum of orginal and copied file
        original_file_checksum = redant.get_md5sum(self.client_list[0],
                                                   "/mnt/huge_file.txt")
        copied_file_checksum = (redant.get_md5sum(self.client_list[0],
                                f"{self.mountpoint}/huge_file.txt"))

        if original_file_checksum.split()[0] != \
           copied_file_checksum.split()[0]:
            raise Exception("md5 checksum of original and copied file are"
                            " different")

        # Remove original huge file
        redant.execute_abstract_op_node("rm -rf /mnt/huge_file.txt",
                                        self.client_list[0])
        self.file_created = False
