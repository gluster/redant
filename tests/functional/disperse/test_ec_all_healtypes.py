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

Description:
    Tests FOps and Data Deletion on a healthy EC volume
"""

from random import choice
from tests.d_parent_test import DParentTest

# disruptive;disp,dist-disp


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        Test steps:
        - Create directory dir1
        - Create files inside dir1
        - Rename all file inside dir1
        - Create softlink and hardlink of files in mountpoint
        - Create tiny, small, medium nd large file
        - Get arequal of dir1
        - Create directory dir2
        - Creating files on dir2
        - Bring down other bricks to max redundancy
        - Create directory dir3
        - Start pumping IO to dir3
        - Validating IO's on dir2 and waiting to complete
        - Bring bricks online
        - Wait for bricks to come online
        - Check if bricks are online
        - Monitor heal completion
        - Get arequal of dir1
        - Compare arequal of dir1
        """

        # Get the bricks from the volume
        bricks_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        client, mpoint = (self.mounts[0]['client'],
                          self.mounts[0]['mountpath'])

        # Creating dir1
        redant.create_dir(mpoint, 'dir1', client)

        # Create files inside dir1
        cmd = (f"cd {mpoint}/dir1/; for i in `seq 1 5`;"
               " do touch file$i; done;")
        redant.execute_abstract_op_node(cmd, client)

        # Rename all files inside dir1
        cmd = (f"cd {mpoint}/dir1/; "
               "for FILENAME in *; do mv $FILENAME Unix_$FILENAME; cd ~;done;")
        redant.execute_abstract_op_node(cmd, client)

        # Create softlink and hardlink of files in mountpoint
        cmd = (f"cd {mpoint}/dir1/; for FILENAME in *; "
               "do ln -s $FILENAME softlink_$FILENAME; cd ~; done;")
        redant.execute_abstract_op_node(cmd, client)

        cmd = (f"cd {mpoint}/dir1/; for FILENAME in *; "
               "do ln $FILENAME hardlink_$FILENAME; cd ~;done;")
        redant.execute_abstract_op_node(cmd, client)

        # Create tiny, small, medium and large file
        # at mountpoint. Offset to differ filenames
        # at diff clients.
        offset = 1
        for mount_obj in self.mounts:
            cmd = f'fallocate -l 100 tiny_file{offset}.txt'
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = f'fallocate -l 20M small_file{offset}.txt'
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = f'fallocate -l 200M medium_file{offset}.txt'
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            cmd = f'fallocate -l 1G large_file{offset}.txt'
            redant.execute_abstract_op_node(cmd, mount_obj['client'])

            offset += 1

        # Get arequal of dir1
        work_dir = f'{mpoint}/dir1'
        result_before_brick_down = redant.collect_mounts_arequal(self.mounts,
                                                                 work_dir)
        # Creating dir2
        redant.create_dir(mpoint, 'dir2', client)

        # Creating files on dir2
        # Write IO
        all_mounts_procs, count = [], 1
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 10, 5, 5,
                                                      mount_obj['client'])
            all_mounts_procs.append(proc)
            count = count + 10

        # Bring down other bricks to max redundancy
        # Bringing bricks offline
        bricks_to_offline = choice(bricks_list)
        redant.bring_bricks_offline(self.vol_name, bricks_to_offline)
        if not redant.are_bricks_offline(self.vol_name, bricks_to_offline,
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_to_offline} is not offline")

        # Creating dir3
        redant.create_dir(mpoint, 'dir2', client)

        # Start pumping IO to dir3
        cmd = (f"cd {mpoint}/dir3; for i in `seq 1 100` ;"
               "do dd if=/dev/urandom of=file$i bs=1M count=5;done")
        redant.execute_abstract_op_node(cmd, client)

        appendcmd = (f"cd {mpoint}/dir3; for i in `seq 1 100` ;"
                     "do dd if=/dev/urandom of=file$i bs=1M "
                     "count=1 oflag=append conv=notrunc;done")

        readcmd = (f"cd {mpoint}/dir3; for i in `seq 1 100` ;"
                   "do dd if=file$i of=/dev/null bs=1M count=5;done")

        redant.execute_abstract_op_node(appendcmd, client)
        redant.execute_abstract_op_node(readcmd, client)

        # Validating IO's on dir2 and waiting to complete
        if not redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO operations failed on some"
                            " or all of the clients")

        # Bring bricks online
        redant.bring_bricks_online(self.vol_name, self.server_list[0],
                                   bricks_to_offline)
        if not redant.are_bricks_online(self.vol_name, bricks_to_offline,
                                        self.server_list[0]):
            raise Exception(f"Brick {bricks_to_offline} is not offline")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal not yet completed")

        # Get arequal of dir1
        result_after_brick_up = redant.collect_mounts_arequal(self.mounts,
                                                              work_dir)
        # Comparing arequals of dir1
        if result_before_brick_down != result_after_brick_up:
            raise Exception("Arequals are not equals before and after "
                            "bringing down redundant bricks")
