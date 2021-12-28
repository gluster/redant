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

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Test Description:
    Tests FOps and Data Deletion on a healthy EC volume
"""

# disruptive;disp,dist-disp

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    def run_test(self, redant):
        """
        Test steps:
        - Create directory dir1
        - Create 5 dir and 5 files in each dir in directory 1
        - Rename all file inside dir1
        - Truncate at any dir in mountpoint inside dir1
        - Create softlink and hardlink of files in mountpoint
        - Delete op for deleting all file in one of the dirs
        - chmod, chown, chgrp inside dir1
        - Create tiny, small, medium nd large file
        - Creating files on client side for dir1
        - Validating IO's and waiting to complete
        - Deleting dir1
        - Check .glusterfs/indices/xattrop is empty
        - Check if brickpath is empty
        """

        # Get the bricks from the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        # Creating dir1
        redant.create_dir(self.mountpoint, 'dir1', self.client_list[0])

        # Create 5 dir and 5 files in each dir at mountpoint on dir1
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
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
                   'do ln -s $FILENAME softlink_$FILENAME;'
                   'done;')
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 1
            cmd = (f'cd {self.mountpoint}/dir1/dir{start + 1}; '
                   'for FILENAME in *; '
                   'do ln $FILENAME hardlink_$FILENAME;'
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

        # Deleting dir1
        cmd = (f'rm -rf -v {self.mountpoint}/*')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check .glusterfs/indices/xattrop is empty
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            cmd = (f"ls -1 {brick_path}/.glusterfs/indices/xattrop/ | "
                   "grep -ve \"xattrop-\" | wc -l")
            ret = redant.execute_abstract_op_node(cmd, brick_node)
            if int(ret['msg'][0].rstrip("\n")) != 0:
                raise Exception(".glusterfs/indices/xattrop"
                                " is not empty")

        # Check if brickpath is empty
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            cmd = (f"ls -1 {brick_path} | wc -l")
            ret = redant.execute_abstract_op_node(cmd,
                                                  brick_node)
            if int(ret['msg'][0].rstrip("\n")) != 0:
                raise Exception(f"Brick path {brick_path} is not empty"
                                f" in node {brick_node}")
