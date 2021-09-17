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
    Check perfromance of ls on distributed volumes
"""

# nonDisruptive;dist-rep,dist-arb,dist-disp
import traceback
from tests.nd_parent_test import NdParentTest


class TestTimeForls(NdParentTest):

    def terminate(self):
        """
        Complete IO on mountpoint, if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.proc_list, self.mounts)):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume of type distributed-replicated or
           distributed-arbiter or distributed-dispersed and start it.
        2. Mount the volume to clients and create 2000 directories
           and 10 files inside each directory.
        3. Wait for I/O to complete on mount point and perform ls
           (ls should complete within 10 seconds).
        """
        self.is_io_running = False
        # Creating 2000 directories on the mount point
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        cmd = ("cd %s; for i in {1..2000};do mkdir dir$i;done"
               % self.mountpoint)
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Create 5000 files inside each directory
        dirs = ('{1..100}', '{101..200}', '{201..300}', '{301..400}',
                '{401..500}', '{501..600}', '{601..700}', '{701..800}',
                '{801..900}', '{901..1000}', '{1001..1100}', '{1101..1200}',
                '{1201..1300}', '{1301..1400}', '{1401..1500}', '{1501..1600}',
                '{1801..1900}', '{1901..2000}')

        self.proc_list, counter = [], 0
        while counter < 18:
            for mount_obj in self.mounts:
                cmd = ("cd %s; for i in %s;"
                       "do touch dir$i/file{1..10};done"
                       % (mount_obj['mountpath'], dirs[counter]))
                proc = redant.execute_command_async(cmd, mount_obj['client'])
                self.proc_list.append(proc)
                counter += 1
        self.is_io_running = True

        # Check if I/O is successful or not
        for proc in self.proc_list:
            ret = redant.wait_till_async_command_ends(proc)
            if ret['error_code'] != 0:
                raise Exception("IO failed")

        self.is_io_running = False

        # Run ls on mount point which should get completed within 10 seconds
        cmd = (f"cd {self.mountpoint}; timeout 10 ls")
        redant.execute_abstract_op_node(cmd, self.client_list[0])
