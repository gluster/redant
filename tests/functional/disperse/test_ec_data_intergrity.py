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
"""

# disruptive;disp,dist-disp

from random import sample
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    def _bring_redundant_bricks_offline(self):
        """
        Bring redundant bricks offline
        """
        brickset_to_offline = []
        # List two bricks in each subvol
        subvols_list = self.redant.get_subvols(self.vol_name,
                                               self.server_list[0])
        if not subvols_list:
            self.redant.logger.error("No Sub-Volumes available for the "
                                     f"volume {self.vol_name}")
            return None

        for subvol in subvols_list:
            brickset_to_offline.extend(sample(subvol, 1))

        # Bring two bricks of each subvol down
        self.redant.bring_bricks_offline(self.vol_name, brickset_to_offline)

        # Validating the bricks are offline
        if not self.redant.are_bricks_offline(self.vol_name,
                                              brickset_to_offline,
                                              self.server_list[0]):
            raise Exception(f"Bricks {brickset_to_offline} are not offline")
        return brickset_to_offline

    def run_test(self, redant):
        """
        Test steps:
        - Create directory dir1
        - Create 5 dir and 5 files in each dir in directory 1
        - Rename all file inside dir1
        - Truncate at any dir in mountpoint inside dir1
        - Create softlink and hardlink of files in mountpoint
        - chmod, chown, chgrp inside dir1
        - Create tiny, small, medium nd large file
        - Creating files on client side for dir1
        - Validating IO's and waiting to complete
        - Get arequal of dir1
        - Bring redundant bricks offline
        - Get arequal of dir1 after 1st set of bricks down
        - Bring redundant bricks offline
        - Get arequal of dir1 after 2nd set of bricks down
        """

        brickset_to_offline = []

        # Creating dir1
        redant.create_dir(self.mountpoint, 'dir1', self.client_list[0])

        # Create 5 dir and 5 files in each dir at mountpoint on dir1
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        start, end = 1, 5
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

            cmd = (f'cd {self.mountpoint}/dir1/dir{start + 1}; '
                   'for FILENAME in *; '
                   'do ln $FILENAME hardlink_$FILENAME;'
                   'done;')
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 5

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

        # Get arequal of dir1
        result_before_bricks_down = (redant.collect_mounts_arequal(
                                     self.mounts, path='dir1/'))

        # Bring redundant bricks offline
        brickset_to_offline = self._bring_redundant_bricks_offline()

        # Get arequal of dir1 after 1st set of bricks down
        result_after_1st_brickset_down = (redant.collect_mounts_arequal(
                                          self.mounts, path='dir1/'))

        # Bring bricks online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          brickset_to_offline):
            raise Exception("unable to bring "
                            f"{brickset_to_offline} online")

        # Wait for brick to come online
        if not (redant.wait_for_volume_process_to_be_online(
                self.vol_name, self.server_list[0],
                self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Check if bricks are online
        offline_brick = redant.get_offline_bricks_list(self.vol_name,
                                                       self.server_list[0])
        if offline_brick:
            raise Exception("All bricks are not online")

        # Bring redundant bricks offline
        brickset_to_offline = self._bring_redundant_bricks_offline()

        # Get arequal of dir1 after 2nd set of bricks down
        result_after_2nd_brickset_down = (redant.collect_mounts_arequal(
                                          self.mounts, path='dir1/'))

        # Comparing arequals
        if result_before_bricks_down != result_after_1st_brickset_down:
            raise Exception('Arequals are not equals before brickset '
                            'down and after 1st brickset down')

        if result_after_2nd_brickset_down != result_after_1st_brickset_down:
            raise Exception('Arequals are not equals before 2nd set '
                            'brick down and after 1st set brick down')
