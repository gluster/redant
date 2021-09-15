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
    Tests File Operations on an EC volume when redundant bricks are
    brought down
"""

# disruptive;disp,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestFopsBrickdown(DParentTest):
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

            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mounts)):
                    raise Exception("Failed to wait for IO to complete")
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
        - 7.chmod, chown, chgrp inside dir1
        - 8.Create tiny, small, medium nd large file
        - 9.Creating files on client side for dir1
        - 10.Brick redundant bricks down
        - 11.Validating IO's and waiting to complete
        - 12.Creating dir2
        - 13.Creating files on client side for dir2
        - 14.Bring bricks online
        - 15.Wait for brick to come online
        - 16.Check if bricks are online
        - 17.Monitor heal completion
        - 18.Validating IO's and waiting to complete
        """
        self.io_mem_monitor_running = False
        self.is_io_running = False
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
               'cd ~;done;')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Truncate at any dir in mountpoint inside dir1
        # start is an offset to be added to dirname to act on
        # diff files at diff clients.
        start = 1
        for mount_obj in self.mounts:
            cmd = (f'cd {self.mountpoint}/dir1/dir{start}/; '
                   'for FILENAME in *; do echo > $FILENAME; cd ~;done;')
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 5
        # Create softlink and hardlink of files in mountpoint
        start = 1
        for mount_obj in self.mounts:
            cmd = (f'cd {self.mountpoint}/dir1/dir{start}; '
                   'for FILENAME in *; '
                   'do ln -s $FILENAME softlink_$FILENAME; cd ~;'
                   'done;')
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 1
            cmd = (f'cd {self.mountpoint}/dir1/dir{start + 1}; '
                   'for FILENAME in *; '
                   'do ln $FILENAME hardlink_$FILENAME; cd ~;'
                   'done;')
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

        # Creating files on client side for dir1
        # Write IO
        self.all_mounts_procs, count = [], 1
        for mount_obj in self.mounts:
            path = f"{mount_obj['mountpath']}/dir1"
            proc = redant.create_deep_dirs_with_files(path,
                                                      count, 2, 10, 5, 5,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count = count + 10
        self.is_io_running = True

        # Bring down other bricks to max redundancy
        # Bringing bricks offline
        redant.bring_bricks_offline(self.vol_name, bricks_list[0:2])
        if not redant.are_bricks_offline(self.vol_name, bricks_list[0:2],
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_list[0:2]} is not offline")

        # Validating IO's and waiting to complete
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed on the mounts")
        self.is_io_running = False

        # Creating dir2
        redant.create_dir(self.mountpoint, 'dir2', self.client_list[0])

        # Creating files on client side for dir2
        # Write IO
        self.all_mounts_procs, count = [], 1
        for mount_obj in self.mounts:
            path = f"{mount_obj['mountpath']}/dir2"
            proc = redant.create_deep_dirs_with_files(path,
                                                      count, 2, 10, 5, 5,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count = count + 10
        self.is_io_running = True

        # Bring bricks online
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_list[0:2])
        if not redant.are_bricks_online(self.vol_name, bricks_list[0:2],
                                        self.server_list[0]):
            raise Exception(f"Brick {bricks_list[0:2]} is not online")

        # Check if bricks are online
        offline_brick = redant.get_offline_bricks_list(self.vol_name,
                                                       self.server_list[0])
        if offline_brick:
            raise Exception("All bricks are not online")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal not yet completed")

        # Validating IO's and waiting to complete
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed on the mounts")
        self.is_io_running = False

        # Check file exist for memory log
        ret = redant.path_exists(self.server_list[0],
                                 self.log_file_mem_monitor)
        if not ret:
            raise Exception("Unexpected:Memory log file does not exist")

        for proc in self.cmd_list_procs:
            ret = redant.wait_till_async_command_ends(proc)
            if ret['error_code'] != 0:
                raise Exception("Memory logging failed")
        self.io_mem_monitor_running = False
