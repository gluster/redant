"""
Copyright (C) 2020-2021 Red Hat, Inc. <http://www.redhat.com>

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
    This test case deals with testing split-brain issue.

"""

# disruptive;arb,dist-arb

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        # Skip if upstream installation
        self.redant.check_gluster_installation(self.server_list, "downstream")

        # Create and start the volume
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node("mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def _perform_io(self, passed: bool):
        # Write IO's
        self.proc = (self.redant.
                     create_files(num_files=1,
                                  fix_fil_size="1k",
                                  path=self.mnt_list[0]['mountpath'],
                                  node=self.mnt_list[0]['client'],
                                  base_file_name="test_file"))
        # Validate IO
        ret = self.redant.validate_io_procs(self.proc, self.mnt_list[0])
        if not passed:
            if ret:
                raise Exception("IO validation passed successfully "
                                "in split-brain")
        else:
            if not ret:
                raise Exception("IO validation failed")

    def run_test(self, redant):

        """
        Description: Create split-brain on files and check if IO's fail
        - Disable self-heal and cluster-quorum-type
        - Get the bricks from the volume
        - Write IO and validate IO
        - Bring 1st set of brick offline(1 Data brick and arbiter brick)
        - Write IO and validate IO
        - Bring 2nd set of bricks offline(1 Data brick and arbiter brick)
        - Write IO and validate IO
        - Check volume is in split-brain
        - Write IO and validate IO - should fail
        - Enable self-heal and cluster-quorum-type
        - Write IO and validate IO - should fail
        """
        # Disable self-heal and cluster-quorum-type
        options = {"self-heal-daemon": "off",
                   "cluster.quorum-type": "none"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Get the bricks from the volume
        sub_vols = redant.get_subvols(self.vol_name,
                                      self.server_list[0])
        self.bricks_to_bring_offline = list(sub_vols[0])
        # Write IO's
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self._perform_io(True)

        # Bring 1st set of brick offline(1 Data brick and arbiter brick)
        for bricks in ((0, -1), (1, -1)):
            down_bricks = []
            for brick in bricks:
                down_bricks.append(self.bricks_to_bring_offline[brick])

            # bring bricks offline
            redant.bring_bricks_offline(self.vol_name, down_bricks)
            if not self.redant.are_bricks_offline(self.vol_name,
                                                  down_bricks,
                                                  self.server_list[0]):
                raise Exception(f"Bricks {down_bricks} "
                                f"are not offline")
            self._perform_io(True)

            # Bring bricks online
            self.redant.bring_bricks_online(self.vol_name,
                                            self.server_list,
                                            down_bricks)

            if not self.redant.are_bricks_online(self.vol_name,
                                                 down_bricks,
                                                 self.server_list[0]):
                raise Exception(f"Bricks {down_bricks} "
                                f"are not online")

        # Check volume is in split-brain
        if not redant.is_volume_in_split_brain(self.server_list[0],
                                               self.vol_name):
            raise Exception("Volume is not in split-brain state")

        # Write IO's
        self._perform_io(False)
        # Enable self-heal and cluster-quorum-type
        options = {"self-heal-daemon": "on",
                   "cluster.quorum-type": "auto"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])
        # Write IO's
        self._perform_io(False)
