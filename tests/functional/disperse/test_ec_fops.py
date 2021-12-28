"""
Copyright (C) 2019-2020  Red Hat, Inc. <http://www.redhat.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Test Description:
    Tests File Operations on a healthy EC volume
"""

import traceback
from tests.d_parent_test import DParentTest

# disruptive;disp,dist-disp


class TestFops(DParentTest):
    def terminate(self):
        """
        Complete memory logging proc if TC fails
        """
        try:
            if self.io_mem_monitor_running:
                for proc in self.cmd_list_procs:
                    self.redant.wait_till_async_command_ends(proc)
            for server in self.server_list:
                cmd = f"rm -f {self.log_file_mem_monitor}"
                self.redant.execute_abstract_op_node(cmd, server, False)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        - 1.Start resource consumption tool
        - 2.Create directory dir1
        - 3.Create 5 dir and 5 files in each dir in directory 1
        - 4.Rename all file inside dir1
        - 5.Truncate at any dir in mountpoint inside dir1
        - 6.Create softlink and hardlink of files in mountpoint
        - 7.Delete op for deleting all file in one of the dirs
        - 8.chmod, chown, chgrp inside dir1
        - 9.Create tiny, small, medium nd large file
        - 10.Creating files on client side for dir1
        - 11.Validating IO's and waiting to complete
        - 12.Get areequal before killing the brick
        - 13.Killing 1st brick manually
        - 14.Get areequal after killing 1st brick
        - 15.Killing 2nd brick manually
        - 16.Get areequal after killing 2nd brick
        - 17.Getting arequal and comparing the arequals
        - 18.Deleting dir1
        """
        self.io_mem_monitor_running = False
        self.cmd_list_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Starting resource consumption using top
        self.log_file_mem_monitor = '/var/log/glusterfs/mem_usage.log'
        cmd = ("for i in {1..20};do top -n 1 -b|egrep "
               " 'RES|gluster' & free -h 2>&1 >> "
               f"{self.log_file_mem_monitor} ;sleep 10;done")
        for mount_obj in self.mounts:
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.cmd_list_procs.append(proc)
        self.io_mem_monitor_running = True

        # get the bricks from the volume
        bricks_list = []
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        # Creating dir1
        redant.create_dir(self.mountpoint, 'dir1', self.client_list[0])

        # Create 5 dir and 5 files in each dir at mountpoint on dir1
        start = 1
        end = 5
        for mount_obj in self.mounts:
            # Number of dir and files to be created.
            # Create dir 1-5 at mountpoint.
            cmd = (f"for ((i={start}; i<={end}; i++)); do "
                   f"mkdir {self.mountpoint}/dir1/dir$i; done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            # Create files inside each dir.
            cmd = (f"for ((i={start}; i<={end}; i++)); do "
                   f"for ((j={start}; j<={end}; j++)); do "
                   f"touch {self.mountpoint}/dir1/dir$i/file$j;"
                   "done; done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            # Increment counter so that at next client dir and files are made
            # with diff offset. Like at next client dir will be named
            # dir6, dir7...dir10. Same with files.
            start += 5
            end += 5

        # Rename all files inside dir1 at mountpoint on dir1
        cmd = (f'cd {self.mountpoint}/dir1/dir1/; '
               'for FILENAME in *; do mv $FILENAME Unix_$FILENAME;'
               'done;')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Truncate at any dir in mountpoint inside dir1
        # start is an offset to be added to dirname to act on
        # diff files at diff clients.
        start = 1
        for mount_obj in self.mounts:
            cmd = (f'cd {self.mountpoint}/dir1/dir{start}/; '
                   'for FILENAME in *; do echo > $FILENAME; done;')
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 5

        # Create softlink and hardlink of files in mountpoint
        start = 1
        for mount_obj in self.mounts:
            cmd = (f'cd {self.mountpoint}/dir1/dir{start}; '
                   'for FILENAME in *; '
                   'do ln -s $FILENAME softlink_$FILENAME; done;')

            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 1
            cmd = (f'cd {self.mountpoint}/dir1/dir{start + 1}; '
                   'for FILENAME in *; '
                   'do ln $FILENAME hardlink_$FILENAME; done;')
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 4

        # chmod, chown, chgrp inside dir1
        # start and end used as offset to access diff files
        # at diff clients.
        start, end = 2, 5
        for mount_obj in self.mounts:
            cmd = (f"for ((i={start}; i<={end}; i++)); do "
                   f"for ((j={start}; j<={end}; j++)); do "
                   f"chmod 777 {mount_obj['mountpath']}/dir1/dir$i/file$j ;"
                   "done; done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = (f"for ((i={start}; i<={end}; i++)); do "
                   f"for ((j={start}; j<={end}; j++)); do "
                   f"chown root {mount_obj['mountpath']}/dir1/dir$i/file$j;"
                   "done; done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = (f"for ((i={start}; i<={end}; i++)); do "
                   f"for ((j={start}; j<={end}; j++)); do "
                   f"chgrp root {mount_obj['mountpath']}/dir1/dir$i/file$j;"
                   "done; done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 5
            end += 5

        # Create tiny, small, medium and large file
        # at mountpoint. Offset to differ filenames
        # at diff clients.
        offset = 1
        for mount_obj in self.mounts:
            cmd = f'fallocate -l 100 {self.mountpoint}/tiny_file{offset}.txt'
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = f'fallocate -l 20M {self.mountpoint}/small_file{offset}.txt'
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = f'fallocate -l 200M {self.mountpoint}/med_file{offset}.txt'
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = f'fallocate -l 1G {self.mountpoint}/large_file{offset}.txt'
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            offset += 1

        # Creating 2TB file if volume is greater
        # than equal to 3TB
        avail = redant.get_size_of_mountpoint(self.mountpoint,
                                              self.client_list[0])
        if int(avail) >= 3000000000:
            cmd = f'fallocate -l 2TB {self.mountpoint}/tiny_file_large.txt'
            redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Creating files on client side for dir1
        # Write IO
        all_mounts_procs, count = [], 1
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 10, 5, 5,
                                                      mount_obj['client'])
            all_mounts_procs.append(proc)
            count = count + 10

        # Validating IO's and waiting to complete
        if not redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO failed on the mounts")

        # Get areequal before killing the brick
        result_before_killing_brick = (redant.collect_mounts_arequal(
                                       self.mounts[0]))

        # Kill 1st brick manually
        redant.bring_bricks_offline(self.vol_name, bricks_list[0])

        # Validating the bricks are offline
        if not redant.are_bricks_offline(self.vol_name, bricks_list[0],
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_list[0]} are not offline")

        # Get areequal after killing 1st brick
        result_after_killing_brick = (redant.collect_mounts_arequal(
                                      self.mounts[0]))

        # Kill 2nd brick manually
        redant.bring_bricks_offline(self.vol_name, bricks_list[1])

        # Validating the bricks are offline
        if not redant.are_bricks_offline(self.vol_name, bricks_list[1],
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_list[1]} are not offline")

        # Get areequal after killing 2nd brick
        result_after_killing_brick_2 = (redant.collect_mounts_arequal(
                                        self.mounts[0]))

        # Comparing areequals
        if result_before_killing_brick != result_after_killing_brick:
            raise Exception('Areequals are not equals before killing brick'
                            'processes and after offlining 1 redundant bricks')

        # Comparing areequals
        if result_after_killing_brick != result_after_killing_brick_2:
            raise Exception('Areequals are not equals after killing 2'
                            ' bricks')

        # Delete op for deleting all file in one of the dirs. start is being
        # used as offset like in previous testcase in dir1
        start = 1
        for mount_obj in self.mounts:
            cmd = (f'cd {self.mountpoint}/dir1/dir{start}/; '
                   'for FILENAME in *; do rm -f $FILENAME; done;')
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 5

        # Deleting dirs
        cmd = (f'rm -rf -v {self.mountpoint}/*')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Close connection and check file exist for memory log
        ret = redant.path_exists(self.client_list[0],
                                 self.log_file_mem_monitor)
        if not ret:
            raise Exception("Unexpected:Memory log file does not exist")

        for proc in self.cmd_list_procs:
            ret = redant.wait_till_async_command_ends(proc)
            if ret['error_code'] != 0:
                raise Exception("Memory logging failed")
        self.io_mem_monitor_running = False
