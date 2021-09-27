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

Description: Tests to check that there is no data loss when rename is
             performed with a brick of volume down.
"""
# nonDisruptive;rep,arb,dist-arb,dist-rep

from random import choice
from time import sleep
from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
         Steps :
         1) Create a volume.
         2) Mount the volume using FUSE.
         3) Create 1000 files on the mount point.
         4) Create the soft-link for file{1..100}
         5) Create the hard-link for file{101..200}
         6) Check for the file count on the mount point.
         7) Begin renaming the files, in multiple iterations.
         8) Let few iterations of the rename complete successfully.
         9) Then while rename is still in progress, kill a brick part of the
            volume.
         10) Let the brick be down for sometime, such that the a couple
             of rename iterations are completed.
         11) Bring the brick back online.
         12) Wait for the IO to complete.
         13) Check if there is any data loss.
         14) Check if all the files are renamed properly.
         """
        # Creating 1000 files on volume root
        mpoint = self.mountpoint
        client = self.client_list[0]
        command = f'touch {mpoint}/file{{1..1000}}_0'
        redant.execute_abstract_op_node(command, client)

        # Create soft links for a few files
        for i in range(1, 100):
            if not (redant.create_link_file(client, f'{mpoint}/file{i}_0',
                                            f'{mpoint}/soft_link_file{i}_0',
                                            True)):
                raise Exception("Unable to create soft link file.")

        # Create hard links for a few files
        for i in range(101, 200):
            if not (redant.create_link_file(client, f'{mpoint}/file{i}_0',
                                            f'{mpoint}/hard_link_file{i}_0')):
                raise Exception("Unable to create hard link file.")

        # Calculate file count for the mount-point
        cmd = (f"ls -lR {mpoint}/ | wc -l")
        ret = redant.execute_abstract_op_node(cmd, client)
        count_before = int(ret['msg'][0].strip())

        # Start renaming the files in multiple iterations
        all_mounts_procs = []
        cmd = ('for i in `seq 1 1000`; do for j in `seq 0 5`;'
               f'do mv -f {mpoint}/file$i\\_$j mpoint/file$i\\_$(expr $j + 1);'
               'done; done')
        proc = redant.execute_command_async(cmd, client)
        all_mounts_procs.append(proc)

        # Waiting for some time for a iteration of rename to complete
        sleep(120)

        # Get the information about the bricks part of the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        # Kill a brick part of the volume
        bricks_offline = choice(bricks_list)
        redant.bring_bricks_offline(self.vol_name, bricks_offline)
        if not redant.are_bricks_offline(self.vol_name, bricks_offline,
                                         self.server_list[0]):
            raise Exception(f"Brick {bricks_offline} is not offline")

        # Let the brick be down for some time
        sleep(60)

        # Bring the brick online using gluster v start force
        redant.volume_start(self.vol_name, self.server_list[0],
                            force=True)

        # Close connection and check if rename has completed
        redant.wait_till_async_command_ends(proc)

        # Do lookup on the files
        # Calculate file count from mount
        cmd = (f"ls -lR {mpoint}/ | wc -l")
        ret = redant.execute_abstract_op_node(cmd, client)
        count_after = int(ret['msg'][0].strip())

        # Check if there is any data loss
        if count_before != count_after:
            raise Exception("The file count before and after"
                            " rename is not same. There is data loss.")

        # Checking if all files were renamed Successfully
        vol_info_dict = redant.get_volume_type_info(self.server_list[0],
                                                    self.vol_name)
        vol_type = vol_info_dict['volume_type_info']['typeStr']
        if vol_type in ("Replicate", "Distributed-Replicate",
                        "Arbiter", "Distribute-Arbiter"):
            cmd = (f"ls -lR {mpoint}/file* | wc -l")
            ret = redant.execute_abstract_op_node(cmd, client)
            count = int(ret['msg'][0].strip())
            if count != 1000:
                raise Exception("Rename failed on some files")
