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
    This test case deals with testing nuke path.
# nonDisruptive;dist-rep,dist-arb,dist-disp,dist
"""

# nonDisruptive;dist-disp

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):

    def run_test(self, redant):
        """
        Test case:
        1. Create a distributed volume, start and mount it
        2. Create 1000 dirs and 1000 files under a directory say 'dir1'
        3. Set xattr glusterfs.dht.nuke to "test" for dir1
        4. Validate dir-1 is not seen from mount point
        5. Validate if the entry is moved to '/brickpath/.glusterfs/landfill'
           and deleted eventually.
        """
        # Assign a variable for the first_client
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        self.first_client = self.mounts[0]['client']

        # Create 1000 dirs and 1000 files under a directory say 'dir1'
        self.dir_1_path = f"{self.mounts[0]['mountpath']}/dir1/"
        redant.create_dir(self.mounts[0]['mountpath'], "dir1",
                          self.first_client)
        cmd = (f"cd {self.dir_1_path};for i in `seq 1 1000`;"
               "do mkdir dir$i;touch file$i;done")
        redant.execute_abstract_op_node(cmd, self.first_client)

        # Set xattr glusterfs.dht.nuke to "test" for dir1
        redant.set_fattr(self.dir_1_path,
                         'glusterfs.dht.nuke',
                         self.first_client, 'test')

        # Validate dir-1 is not seen from mount point
        ret = redant.get_dir_contents(self.mounts[0]['mountpath'],
                                      self.first_client)
        if ret != []:
            raise Exception("UNEXPECTED: Mount point has files ideally "
                            "it should be empty.")

        # Validate if the entry is moved to '/brickpath/.glusterfs/landfill'
        # and deleted eventually
        bricks_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to fetch the bricks list")

        for brick_path in bricks_list:
            node, path = brick_path.split(":")
            path = f"{path}/.glusterfs/landfill/*/"
            ret = redant.get_dir_contents(path, node)
            # In case if landfile is already cleaned before checking
            # stop execution of the loop.
            if ret is None:
                redant.logger.info("Bricks have been already cleaned up.")
                break
