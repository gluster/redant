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
    TC to check deletion of files having self-pointing links
"""

# disruptive;dist
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestDeletDirWithSelfPointingLinktofiles(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 2
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def run_test(self, redant):
        """
        Test case:
        1. Create a pure distribute volume with 2 bricks, start and mount it.
        2. Create dir dir0/dir1/dir2 inside which create 1000 files and rename
           all the files.
        3. Start remove-brick operation on the volume.
        4. Check remove-brick status till status is completed.
        5. When remove-brick status is completed stop it.
        6. Go to brick used for remove brick and perform lookup on the files.
        8. Change the linkto xattr value for every file in brick used for
           remove brick to point to itself.
        9. Perfrom rm -rf * from mount point.
        """
        # Create dir /dir0/dir1/dir2
        self.dir_path = f"{self.mountpoint}/dir0/dir1/dir2/"
        redant.create_dir(self.mountpoint, "dir0/dir1/dir2",
                          self.client_list[0])

        # Create 1000 files inside /dir0/dir1/dir2
        cmd = (f"cd {self.dir_path}; for i in {{1..1000}}; do echo "
               "'Test file' > tfile-$i; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Rename 1000 files present inside /dir0/dir1/dir2
        cmd = (f"cd {self.dir_path}; for i in {{1..1000}}; do mv "
               "tfile-$i ntfile-$i; done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Start remove-brick operation on the volume
        brick = redant.form_bricks_list_to_remove_brick(self.server_list[0],
                                                        self.vol_name,
                                                        subvol_num=1)
        if not brick:
            raise Exception("Brick_list to be removed is empty")

        redant.remove_brick(self.server_list[0], self.vol_name, brick,
                            'start')

        # Check remove-brick status till status is completed
        ret = redant.wait_for_remove_brick_to_complete(self.server_list[0],
                                                       self.vol_name, brick)
        if not ret:
            raise Exception("Remove-brick didn't complete on volume")

        # When remove-brick status is completed stop it
        redant.remove_brick(self.server_list[0], self.vol_name, brick,
                            'stop')

        # Go to brick used for remove brick and perform lookup on the files
        node, path = brick[0].split(":")
        path = f"{path}/dir0/dir1/dir2/"
        redant.execute_abstract_op_node(f"ls {path}*", node)

        # Change the linkto xattr value for every file in brick used for
        # remove brick to point to itself
        file_list = redant.get_dir_contents(path, node)
        if not file_list:
            raise Exception("Unable to get files present in dir0/dir1/dir2")

        ret = redant.get_dht_linkto_xattr(node, f"{path}{file_list[0]}")
        if not ret:
            raise Exception("Unable to fetch dht linkto xattr")
        linkto_xattr = ret[1].split('=')[1].strip()

        # Change trusted.glusterfs.dht.linkto from dist-client-0 to
        # dist-client-1 or visa versa according to initial value
        dht_linkto_xattr = linkto_xattr[1:-1].split("-")
        if int(dht_linkto_xattr[3]):
            dht_linkto_xattr[3] = "0"
        else:
            dht_linkto_xattr[3] = "1"
        linkto_value = "-".join(dht_linkto_xattr)

        # Set xattr trusted.glusterfs.dht.linkto on all the linkto files
        ret = redant.set_fattr(f"{path}*", 'trusted.glusterfs.dht.linkto',
                               node, linkto_value)
        if ret['error_code'] != 0:
            raise Exception("Failed to change linkto file to point to itself")

        # Perfrom rm -rf * from mount point
        redant.execute_abstract_op_node(f"rm -rf {self.mountpoint}/*",
                                        self.client_list[0])
