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
"""

# disruptive;dist

from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 1
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _check_permissions_of_dir(self):
        """Check permissions of dir created."""
        bricks = self.redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        for brick_path in bricks:
            node, path = brick_path.split(":")
            ret = self.redant.get_file_stat(node, "{}/dir".format(path))
            if not ret:
                raise Exception("Not able to get stat of the dir")
            if int(ret['msg']['permission']) != 755:
                raise Exception("Unexpected:Permissions of dir is "
                                f"{ret['msg']['permission']} not 755")

    def _check_trusted_glusterfs_dht_on_all_bricks(self):
        """Check trusted.glusterfs.dht xattr on the backend bricks"""
        bricks = self.redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        possible_values = ["0x000000000000000000000000ffffffff",
                           "0x00000000000000000000000000000000"]
        for brick_path in bricks:
            node, path = brick_path.split(":")
            dir_name = f"{path}/dir"
            ret = self.redant.get_fattr(dir_name, "trusted.glusterfs.dht",
                                        node)
            fattr = ret[1].split("=")[1].strip()
            if fattr != possible_values[bricks.index(brick_path)]:
                raise Exception("Value of trusted.glusterfs.dht "
                                "is not as expected")

    def run_test(self, redant):
        """
        Test case:
        1. Create a 1 brick pure distributed volume.
        2. Start the volume and mount it on a client node using FUSE.
        3. Create a directory on the mount point.
        4. Check trusted.glusterfs.dht xattr on the backend brick.
        5. Add brick to the volume using force.
        6. Do lookup from the mount point.
        7. Check the directory permissions from the backend bricks.
        8. Check trusted.glusterfs.dht xattr on the backend bricks.
        9. From mount point cd into the directory.
        10. Check the directory permissions from backend bricks.
        11. Check trusted.glusterfs.dht xattr on the backend bricks.
        """
        # Create a directory on the mount point
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        redant.create_dir(self.mounts[0]['mountpath'], "dir",
                          self.client_list[0])

        # Check trusted.glusterfs.dht xattr on the backend brick
        self._check_trusted_glusterfs_dht_on_all_bricks()

        # Add brick to the volume using force
        brick = redant.form_brick_cmd_to_add_brick(self.server_list[0],
                                                   self.vol_name,
                                                   self.server_list,
                                                   self.brick_roots)
        if brick is None:
            raise Exception("Failed to form brick list to add brick")

        redant.add_brick(self.vol_name, brick, self.server_list[0],
                         force=True)

        # Do a lookup from the mount point
        cmd = f"ls -lR {self.mountpoint}/dir"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check the directory permissions from the backend bricks
        self._check_permissions_of_dir()

        # Check trusted.glusterfs.dht xattr on the backend bricks
        self._check_trusted_glusterfs_dht_on_all_bricks()

        # From mount point cd into the directory
        cmd = f"cd {self.mountpoint}/dir; cd ..; cd {self.mountpoint}/dir"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check the directory permissions from backend bricks
        self._check_permissions_of_dir()

        # Check trusted.glusterfs.dht xattr on the backend bricks
        self._check_trusted_glusterfs_dht_on_all_bricks()
