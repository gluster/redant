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
    TC checks if a file can be opened and accessed if the dht
    layout has become stale.
"""

# disruptive;dist
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestAccessFileStaleLayout(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Check if 2 clients available
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=2)

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 2
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list[0:2]:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

    def _get_brick_node_and_path(self):
        """Yields list containing brick node and path from first brick of
           each subvol
        """
        subvols = self.redant.get_subvols(self.vol_name, self.server_list[0])
        for subvol in subvols:
            subvol[0] += self.dir_path
            yield subvol[0].split(':')

    def _assert_file_lookup(self, node, fqpath, when, result):
        """Perform `stat` on `fqpath` from `node` and validate against
           `result`
        """
        cmd = f"stat {fqpath}"
        ret = self.redant.execute_abstract_op_node(cmd, node, False)
        expected_val = -1
        assert_msg = 'fail'
        if result:
            if ret['error_code'] != 0:
                raise Exception(f"Lookup on {fqpath} from {node} should"
                                f" pass {when} layout")
            return 0
        if ret['error_code'] == 0:
            raise Exception(f"Lookup on {fqpath} from {node} should"
                            f" fail {when} layout")
        return 0

    def run_test(self, redant):
        """
        Steps:
        1. Create, start and mount a volume consisting 2 subvols on 2 clients
        2. Create a dir `dir` and file `dir/file` from client0
        3. Take note of layouts of `brick1`/dir and `brick2`/dir of the volume
        4. Validate for success lookup from only one brick path
        5. Re-assign layouts ie., brick1/dir to brick2/dir and vice-versa
        6. Remove `dir/file` from client0 and recreate same file from client0
           and client1
        7. Validate for success lookup from only one brick path (as layout is
           changed file creation path will be changed)
        8. Validate checksum is matched from both the clients
        """
        # Will be used in _get_brick_node_and_path
        self.dir_path = '/dir'

        # Will be used in argument to _assert_file_lookup
        file_name = '/file'

        dir_path = f"{self.mountpoint}{self.dir_path}"
        file_path = f"{dir_path}{file_name}"

        client0, client1 = self.client_list[0], self.client_list[1]
        fattr = 'trusted.glusterfs.dht'
        io_cmd = ("cat /dev/urandom | tr -dc [:space:][:print:] | "
                  f"head -c 1K > {file_path}")

        # Create a dir from client0
        redant.create_dir(self.mountpoint, "dir", client0)

        # Touch a file with data from client0
        redant.execute_abstract_op_node(io_cmd, client0)

        # Yields `node` and `brick-path` from first brick of each subvol
        gen = self._get_brick_node_and_path()

        # Take note of newly created directory's layout from org_subvol1
        node1, fqpath1 = next(gen)
        layout1 = redant.get_fattr(fqpath1, fattr, node1)
        if not layout1:
            raise Exception(f"{fattr} is not present on {fqpath1}")

        # Lookup on file from node1 should fail as `dir/file` will always get
        # hashed to node2 in a 2-brick distribute volume by default
        self._assert_file_lookup(node1, f"{fqpath1}{file_name}",
                                 when='before', result=False)

        # Take note of newly created directory's layout from org_subvol2
        node2, fqpath2 = next(gen)
        layout2 = redant.get_fattr(fqpath2, fattr, node2)
        if not layout1:
            raise Exception(f"{fattr} is not present on {fqpath2}")

        # Lookup on file from node2 should pass
        self._assert_file_lookup(node2, f"{fqpath2}{file_name}",
                                 when='before', result=True)

        # Set org_subvol2 directory layout to org_subvol1 and vice-versa
        for node, fqpath, layout, vol in ((node1, fqpath1, layout2, (2, 1)),
                                          (node2, fqpath2, layout1, (1, 2))):
            ret = redant.set_fattr(fqpath, fattr, node, layout)
            if ret['error_code'] != 0:
                raise Exception(f"Failed to set layout of org_subvol{vol[0]}"
                                f"brick {fqpath} of org_subvol{vol[1]}")

        # Remove file after layout change from client0
        cmd = f"rm -f {file_path}"
        redant.execute_abstract_op_node(io_cmd, client0)

        # Create file with same name as above after layout change from client0
        # and client1
        for client in (client0, client1):
            redant.execute_abstract_op_node(cmd, client)

        # After layout change lookup on file from node1 should pass
        self._assert_file_lookup(node1, f"{fqpath1}{file_name}",
                                 when='after', result=True)

        # After layout change lookup on file from node2 should fail
        self._assert_file_lookup(node2, f"{fqpath2}{file_name}",
                                 when='after', result=False)

        # Take note of checksum from client0 and client1
        checksums = [None] * 2
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for index, mount in enumerate(self.mounts):
            checksums[index] = redant.collect_mounts_arequal(mount, "dir")

        # Validate no checksum mismatch
        if not checksums[0] and checksums[0] != checksums[1]:
            raise Exception('Checksum mismatch between client0 and client1')
