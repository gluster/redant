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

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Calculate the usable size and fill till it reachs min free limit
        3. Rename the file
        4. Try to perfrom I/O from mount point.(This should fail)
        """
        bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])

        # Calculate the usable size and fill till it reachs
        # min free limit
        usable_size = redant.get_usable_size_per_disk(bricks[0])
        if not usable_size:
            raise Exception("Failed to get the usable size of the brick")

        cmd = f"fallocate -l {usable_size-1}G {self.mountpoint}/file"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Rename the file
        cmd = f"mv {self.mountpoint}/file {self.mountpoint}/Renamedfile"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Try to perfrom I/O from mount point(This should fail)
        cmd = f"fallocate -l 5G {self.mountpoint}/mfile"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Able to do I/O even when disks are "
                            "filled to min free limit")
