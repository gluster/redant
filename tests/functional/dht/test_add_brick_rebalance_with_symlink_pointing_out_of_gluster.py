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
    TC to check add brick when files in volume have symlink pointing out
    of it
"""

# disruptive;dist-rep,dist-arb
import traceback
from tests.d_parent_test import DParentTest


class TestAddBrickRebalanceWithSymlinkPointingOutOfGluster(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_copy_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.proc, self.mounts)):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create symlinks on the volume such that the files for the symlink
           are outside the volume.
        3. Once all the symlinks are create a data file using dd:
           dd if=/dev/urandom of=FILE bs=1024 count=100
        4. Start copying the file's data to all the symlink.
        5. When data is getting copied to all files through symlink add brick
           and start rebalance.
        6. Once rebalance is complete check the md5sum of each file through
           symlink and compare if it's same as the orginal file.
        """
        self.is_copy_running = False
        # Create symlinks on volume pointing outside volume
        cmd = (f"cd {self.mountpoint}; mkdir -p /mnt/tmp_dir;for i in "
               "{1..100};do touch /mnt/tmp_dir/file$i; ln -sf "
               "/mnt/tmp_dir/file$i link$i;done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create a data file using dd inside mount point
        cmd = (f"cd {self.mountpoint}; dd if=/dev/urandom of=FILE bs=1024"
               " count=100")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Start copying data from file to symliks
        cmd = (f"cd {self.mountpoint};for i in {{1..100}};do cat FILE >> "
               "link$i;done")
        self.proc = redant.execute_command_async(cmd, self.client_list[0])
        self.is_copy_running = True

        # Add brick to volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.volname}")

        # Trigger rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0], force=True)

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=1200)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume "
                            f"{self.vol_name}")

        # Validate if I/O was successful or not.
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        ret = redant.validate_io_procs(self.proc, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")
        self.is_copy_running = False

        # Get md5sum of the original file and compare it with that of
        # all files through the symlink
        original_file_md5sum = redant.get_md5sum(self.client_list[0],
                                                 f"{self.mountpoint}/FILE")
        if original_file_md5sum is None:
            raise Exception('Failed to get md5sum of original file')

        for number in range(1, 101):
            symlink_md5sum = (redant.get_md5sum(self.client_list[0],
                              f"{self.mountpoint}/link{number}"))
            if symlink_md5sum is None:
                raise Exception("Failed to get md5sum")

            if original_file_md5sum.split()[0].strip() != \
               symlink_md5sum.split()[0].strip():
                raise Exception("Original file and symlink checksum not equal"
                                f" for link{number}")
