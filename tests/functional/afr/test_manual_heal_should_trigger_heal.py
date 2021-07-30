"""
 Copyright (C) 2015-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Tc to test if heal is triggered on executing heal manually
"""

# disruptive;dist
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = self.vol_type_inf['dist']
        conf_hash['dist_count'] = 1
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)

    def run_test(self, redant):
        """
        - create a single brick volume
        - add some files and directories
        - get arequal from mountpoint
        - add-brick such that this brick makes the volume a replica vol 1x2
        - start heal
        - make sure heal is completed
        - get arequals from all bricks and compare with arequal from mountpoint
        """
        # Start IO on mounts
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      0, 1, 1, 1, 10,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Get arequal for mount before adding bricks
        arequals = redant.collect_mounts_arequal(self.mounts)
        mount_point_total = arequals[0][-1].split(':')[-1]

        # Form brick list to add
        _, bricks_to_add = redant.form_brick_cmd(self.server_list,
                                                 self.brick_roots,
                                                 self.vol_name, 1,
                                                 True)

        # Add bricks
        redant.add_brick(self.vol_name, bricks_to_add, self.server_list[0],
                         force=True, replica_count=3)

        # Make sure the newly added bricks are available in the volume
        # get the bricks for the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Failed to get the brick list")

        add_brick_list = bricks_to_add.split(" ")
        for brick in add_brick_list:
            if brick not in bricks_list:
                raise Exception(f"Brick {brick} is not in brick list")

        # Make sure volume change from distribute to replicate volume
        vol_info_dict = redant.get_volume_type_info(self.server_list[0],
                                                    self.vol_name)
        vol_type = vol_info_dict['volume_type_info']['typeStr']
        if vol_type != "Replicate":
            raise Exception("Volume type is not converted to Replicate "
                            "after adding bricks")

        # Start healing
        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception("Heal is not started")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal is not yet complete")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequal on bricks and compare with mount_point_total
        # It should be the same
        arequals = redant.collect_bricks_arequal(bricks_list)
        for arequal in arequals:
            brick_total = arequal[-1].split(':')[-1]
            if brick_total != mount_point_total:
                raise Exception("Arequals for mountpoint and brick is not "
                                "equal")
