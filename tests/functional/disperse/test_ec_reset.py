"""
 Copyright (C) 2018-2020  Red Hat, Inc. <http://www.redhat.com>

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

 Description:
    Tests brick reset on a EC volume.
    For brick reset we can start it to kill a brick with source defined
    or commit to reset a brick with source and destination defined
"""

# disruptive;disp,dist-disp
from random import choice
from time import sleep
import traceback
from tests.d_parent_test import DParentTest


class TestBrickReset(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
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
        - Start resource consumption tool
        - Create IO on dir2 of volume mountpoint
        - Reset brick start
        - Check if brick is offline
        - Reset brick with destination same as source with force running IO's
        - Validating IO's and waiting for it to complete on dir2
        - Remove dir2
        - Create 5 directory and 5 files in dir of mountpoint
        - Rename all files inside dir1 at mountpoint
        - Create softlink and hardlink of files in dir1 of mountpoint
        - Delete op for deleting all file in one of the dirs inside dir1
        - Change chmod, chown, chgrp
        - Create tiny, small, medium and large file
        - Create IO's
        - Validating IO's and waiting for it to complete
        - Calculate arequal before kiiling brick
        - Get brick from Volume
        - Reset brick
        - Check if brick is offline
        - Reset brick by giving a different source and dst node
        - Reset brick by giving dst and source same without force
        - Obtain hostname
        - Reset brick with dst-source same force using hostname - Successful
        - Monitor heal completion
        - Bring down other bricks to max redundancy
        - Get arequal after bringing down bricks
        - Bring bricks online
        - Reset brick by giving a same source and dst brick
        - Kill brick manually
        - Check if brick is offline
        - Reset brick by giving a same source and dst brick
        - Wait for brick to come online
        - Bring down other bricks to max redundancy
        - Get arequal after bringing down bricks
        - Bring bricks online
        - Remove brick from backend
        - Check if brick is offline
        - Reset brick by giving dst and source same without force - Successful
        - Monitor heal completion
        - Compare the arequal's calculated
        """
        self.is_io_running = False
        self.io_mem_monitor_running = False
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Starting resource consumption using top
        self.log_file_mem_monitor = '/var/log/glusterfs/mem_usage.log'
        cmd = ("for i in {1..100};do top -n 1 -b|egrep 'RES|gluster' & free -h"
               f" 2>&1 >> {self.log_file_mem_monitor} ; sleep 10;done")

        self.cmd_list_procs = []
        for mount_obj in self.mounts:
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.cmd_list_procs.append(proc)
        self.io_mem_monitor_running = True

        # Get the bricks from the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        # Creating directory2
        redant.create_dir(self.mountpoint, "dir2", self.mounts[0]['client'])

        # Creating files on client side for dir2
        count = 1
        for mount in self.mounts:
            # Create dirs with file
            proc = (redant.create_deep_dirs_with_files(
                    f"{mount['mountpath']}/dir2", count, 2, 2, 2, 20,
                    mount['client']))
            self.all_mounts_procs.append(proc)
            count += 20
        self.is_io_running = True

        # Reset a brick
        brick_reset = choice(bricks_list)
        redant.reset_brick(self.server_list[0], self.vol_name, brick_reset,
                           "start")

        # Check if the brick is offline
        offline_bricks = redant.get_offline_bricks_list(self.vol_name,
                                                        self.server_list[0])
        if offline_bricks != brick_reset:
            raise Exception("Expected Brick is not offline")

        # Reset brick with dest same as source with force while running IO's
        redant.reset_brick(self.server_list[0], self.vol_name, brick_reset,
                           "commit", brick_reset, force="true")

        # Validating IO's and waiting to complete
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")
        self.is_io_running = False

        # List all files and dirs created
        ret = redant.list_all_files_and_dirs_mounts(self.mounts)
        if not ret:
            raise Exception("Failed to list all files and dirs")

        # Deleting dir2
        cmd = f"rm -rf {self.mounts[0]['mountpath']}/dir2"
        redant.execute_abstract_op_node(cmd, self.mounts[0]['client'])

        # Creating dir1
        redant.create_dir(self.mountpoint, "dir1", self.mounts[0]['client'])

        # Create 5 dir and 5 files in each dir at mountpoint on dir1
        start, end = 1, 5
        for mount_obj in self.mounts:
            # Number of dir and files to be created.
            dir_range = ("%s..%s" % (str(start), str(end)))
            file_range = ("%s..%s" % (str(start), str(end)))
            # Create dir 1-5 at mountpoint.
            redant.create_dir(mount_obj['mountpath'], "dir1/dir{%s}"
                              % dir_range, mount_obj['client'])

            # Create files inside each dir.
            cmd = ('touch %s/dir1/dir{%s}/file{%s};'
                   % (mount_obj['mountpath'], dir_range, file_range))
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            # Increment counter so that at next client dir and files are made
            # with diff offset. Like at next client dir will be named
            # dir6, dir7...dir10. Same with files.
            start += 5
            end += 5

        # Rename all files inside dir1 at mountpoint on dir1
        cmd = (f"cd {self.mountpoint}/dir1/dir1/; "
               "for FILENAME in *; do mv $FILENAME Unix_$FILENAME; done;")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Truncate at any dir in mountpoint inside dir1
        # start is an offset to be added to dirname to act on
        # diff files at diff clients.
        start = 1
        for mount_obj in self.mounts:
            cmd = (f"cd {mount_obj['mountpath']}/dir1/dir{start}/; "
                   "for FILENAME in *; do echo > $FILENAME; done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 1

        # Create softlink and hardlink of files in mountpoint. Start is an
        # offset to be added to dirname to act on diff files at diff clients.
        start = 1
        for mount_obj in self.mounts:
            cmd = (f"cd {mount_obj['mountpath']}/dir1/dir{start}; "
                   "for FILENAME in *; do ln -s $FILENAME softlink_$FILENAME;"
                   "done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = (f"cd {mount_obj['mountpath']}/dir1/dir{start + 1}; "
                   "for FILENAME in *; do ln $FILENAME hardlink_$FILENAME;"
                   "done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 5

        # Delete op for deleting all file in one of the dirs. start is being
        # used as offset like in previous testcase in dir1
        start = 1
        for mount_obj in self.mounts:
            cmd = (f"cd {mount_obj['mountpath']}/dir1/dir{start}; "
                   "for FILENAME in *; do rm -f $FILENAME; done;")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 5

        # chmod, chown, chgrp inside dir1
        # start and end used as offset to access diff files
        # at diff clients.
        start, end = 2, 5
        for mount_obj in self.mounts:
            dir_file_range = '%s..%s' % (str(start), str(end))
            cmd = (f"chmod 777 {mount_obj['mountpath']}/dir1/"
                   "dir{%s}/file{%s}" % (dir_file_range, dir_file_range))
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = (f"chown root {mount_obj['mountpath']}/dir1/"
                   "dir{%s}/file{%s}" % (dir_file_range, dir_file_range))
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = (f"chgrp root {mount_obj['mountpath']}/dir1/"
                   "dir{%s}/file{%s}" % (dir_file_range, dir_file_range))
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            start += 5
            end += 5

        # Create tiny, small, medium nd large file
        # at mountpoint. Offset to differ filenames
        # at diff clients.
        offset = 1
        for mount_obj in self.mounts:
            cmd = (f"fallocate -l 100 {mount_obj['mountpath']}/"
                   f"tiny_file{offset}.txt")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = (f"fallocate -l 20M {mount_obj['mountpath']}/"
                   f"small_file{offset}.txt")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = (f"fallocate -l 200M {mount_obj['mountpath']}/"
                   f"medium_file{offset}.txt")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = (f"fallocate -l 1G {mount_obj['mountpath']}/"
                   f"large_file{offset}.txt")
            redant.execute_abstract_op_node(cmd, mount_obj['client'])
            offset += 1

        # Creating files on client side for dir1
        self.all_mounts_procs, count = [], 100
        for mount_obj in self.mounts:
            # Create dirs with file
            proc = (redant.create_deep_dirs_with_files(
                    f"{mount['mountpath']}/dir1", count, 2, 2, 2, 20,
                    mount['client']))
            self.all_mounts_procs.append(proc)
            count += 20

        # Validating IO's and waiting to complete
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")

        # List all files and dirs created
        ret = redant.list_all_files_and_dirs_mounts(self.mounts)
        if not ret:
            raise Exception("Failed to list all files and dirs")

        # Get areequal before killing the brick
        result_before_killing_brick = (redant.collect_mounts_arequal(
                                       self.mounts[0]))

        # Reset a brick
        redant.reset_brick(self.server_list[0], self.vol_name, bricks_list[0],
                           "start")

        # Check if the brick is offline
        offline_bricks = redant.get_offline_bricks_list(self.vol_name,
                                                        self.server_list[0])
        if offline_bricks != bricks_list[0]:
            raise Exception("Expected Brick is not offline")

        # Reset brick by giving a different source and dst brick
        ret = redant.reset_brick(self.server_list[0], self.vol_name,
                                 bricks_list[0], "commit", bricks_list[1],
                                 excep=False)
        if ret['error_code'] == 0:
            raise Exception("Not Expected: Reset brick is successfull")

        # Reset brick with destination same as source
        ret = redant.reset_brick(self.server_list[0], self.vol_name,
                                 bricks_list[0], "commit", bricks_list[0],
                                 excep=False)
        if ret['error_code'] == 0:
            raise Exception("Not Expected: Reset brick is successfull")

        # Obtain hostname of node
        ret = redant.execute_abstract_op_node("hostname", self.server_list[0])
        hostname_node1 = ret['msg'][0].strip()

        # Reset brick with destination same as source with force using hostname
        redant.reset_brick(hostname_node1, self.vol_name, bricks_list[0],
                           "commit", bricks_list[0], force=True)

        # Wait for brick to come online
        ret = redant.wait_for_bricks_to_come_online(self.vol_name,
                                                    self.server_list,
                                                    bricks_list)
        if not ret:
            raise Exception("Bricks are not online")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # Check if bricks are online
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not redant.are_bricks_online(self.vol_name, all_bricks,
                                        self.server_list[0]):
            raise Exception('All bricks are not online')

        # Bring down other bricks to max redundancy
        ret = redant.bring_bricks_offline(self.vol_name, bricks_list[1:3])
        if not ret:
            raise Exception('Bricks are not offline')

        # Check if 4 bricks are online
        all_bricks = []
        all_bricks = [bricks_list[0], bricks_list[3], bricks_list[4],
                      bricks_list[5]]
        ret = redant.are_bricks_online(self.vol_name, all_bricks,
                                       self.server_list[0])
        if not ret:
            raise Exception('All bricks are not online')

        # Check mount point
        cmd = 'ls -lrt /mnt'
        redant.execute_abstract_op_node(cmd, self.mounts[0]['client'])

        # Get arequal after bringing down bricks
        result_offline_redundant_brick1 = (redant.collect_mounts_arequal(
                                           self.mounts[0]))

        # Bring bricks online
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         bricks_list[1:3])
        if not ret:
            raise Exception('Bricks not brought online')

        # Wait for brick to come online
        ret = redant.wait_for_bricks_to_come_online(self.vol_name,
                                                    self.server_list,
                                                    bricks_list[1:3])
        if not ret:
            raise Exception("Bricks are not online")

        # Reset brick without bringing down brick
        ret = redant.reset_brick(self.server_list[0], self.vol_name,
                                 bricks_list[1], "commit", bricks_list[1],
                                 excep=False)
        if ret['error_code'] == 0:
            raise Exception("Not Expected: Reset brick is successfull")

        # Kill the brick manually
        ret = redant.bring_bricks_offline(self.vol_name, bricks_list[1])
        if not ret:
            raise Exception('Brick not offline')

        # Check if the brick is offline
        ret = redant.are_bricks_offline(self.vol_name, bricks_list[1],
                                        self.server_list[0])
        if not ret:
            raise Exception("Brick is not offline")

        # Reset brick with dest same as source after killing brick manually
        redant.reset_brick(self.server_list[0], self.vol_name, bricks_list[1],
                           "commit", bricks_list[1], force=True)

        # Wait for brick to come online
        ret = redant.wait_for_bricks_to_come_online(self.vol_name,
                                                    self.server_list,
                                                    bricks_list[1])
        if not ret:
            raise Exception("Bricks are not online")

        # Check if bricks are online
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not redant.are_bricks_online(self.vol_name, all_bricks,
                                        self.server_list[0]):
            raise Exception('All bricks are not online')

        # Bring down other bricks to max redundancy
        # Bringing bricks offline
        ret = redant.bring_bricks_offline(self.vol_name, bricks_list[2:4])
        if not ret:
            raise Exception('Bricks not offline')

        # Check mount point
        cmd = 'ls -lrt /mnt'
        redant.execute_abstract_op_node(cmd, self.mounts[0]['client'])

        # Get arequal after bringing down bricks
        result_offline_redundant_brick2 = (redant.collect_mounts_arequal(
                                           self.mounts[0]))

        # Bring bricks online
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         bricks_list[2:4])
        if not ret:
            raise Exception('Bricks not brought online')

        # Removing brick from backend
        node, brick = bricks_list[0].split(":")
        cmd = f"rm -rf {brick}"
        redant.execute_abstract_op_node(cmd, node)

        # Check if the brick is offline
        count = 0
        while count <= 20:
            ret = redant.are_bricks_offline(self.vol_name,
                                            bricks_list[0],
                                            self.server_list[0])
            if ret:
                break
            sleep(2)
            count = + 1
        if not ret:
            raise Exception("Brick is not offline")

        # Reset brick with destination same as source
        redant.reset_brick(hostname_node1, self.vol_name, bricks_list[0],
                           "commit", bricks_list[0])

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # Comparing arequals
        if result_before_killing_brick != result_offline_redundant_brick1:
            raise Exception('Arequals are not equals before killing brick'
                            'processes and after offlining redundant bricks')

        # Comparing arequals
        if result_offline_redundant_brick1 != result_offline_redundant_brick2:
            raise Exception('Arequals are not equals for offlining redundant'
                            ' bricks')

        # Deleting dir1
        cmd = f"rm -rf {self.mounts[0]['mountpath']}/dir1"
        redant.execute_abstract_op_node(cmd, self.mounts[0]['mountpath'])
