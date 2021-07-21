"""
 Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
    Test Rebalance should start successfully if name of volume more than 108
    chars
"""

# disruptive;
import traceback
from tests.d_parent_test import DParentTest


class TestLookupDir(DParentTest):

    def terminate(self):
        """
        Revert the changes in glusterd.vol file
        """
        try:
            cmd = ("sed -i '/transport.socket.bind-address/d'"
                   " /etc/glusterfs/glusterd.vol")
            self.redant.execute_abstract_op_node(cmd, self.server_list[0])
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        1. On Node N1, Add "transport.socket.bind-address N1" in the
            /etc/glusterfs/glusterd.vol
        2. Create a replicate (1X3) and disperse (4+2) volumes with
            name more than 108 chars
        3. Mount the both volumes using node 1 where you added the
            "transport.socket.bind-address" and start IO(like untar)
        4. Perform add-brick on replicate volume 3-bricks
        5. Start rebalance on replicated volume
        6. Perform add-brick for disperse volume 6 bricks
        7. Start rebalance of disperse volume
        """
        cmd = ("sed -i 's/end-volume/option transport.socket.bind-address"
               f" {self.server_list[0]}\\n&/g' /etc/glusterfs/glusterd.vol")

        disperse = ("disperse_e4upxjmtre7dl4797wedbp7r3jr8equzvmcae9f55t6z1"
                    "ffhrlk40jtnrzgo4n48fjf6b138cttozw3c6of3ze71n9urnjkshoi")
        replicate = ("replicate_e4upxjmtre7dl4797wedbp7r3jr8equzvmcae9f55t6z1"
                     "ffhrlk40tnrzgo4n48fjf6b138cttozw3c6of3ze71n9urnjskahn")

        volnames = (disperse, replicate)
        for volume, vol_name in (
                ("disperse", disperse), ("replicate", replicate)):

            mul_fac = 6 if volume == "disperse" else 3
            brick_dict, bricks_cmd = redant.form_brick_cmd(self.server_list,
                                                           self.brick_roots,
                                                           volume, mul_fac)
            if volume == "replicate":
                conf_hash = {
                    "dist_count": 1,
                    "replica_count": 3,
                    "transport": "tcp"
                }
                redant.volume_create_with_custom_bricks(replicate,
                                                        self.server_list[0],
                                                        conf_hash, bricks_cmd,
                                                        brick_dict)

            else:
                conf_hash = {
                    "disperse_count": 6,
                    "redundancy_count": 2,
                    "transport": "tcp"
                }
                redant.volume_create_with_custom_bricks(disperse,
                                                        self.server_list[0],
                                                        conf_hash, bricks_cmd,
                                                        brick_dict,
                                                        force=True)

            redant.volume_start(vol_name, self.server_list[0])

        # Add entry in 'glusterd.vol'
        redant.execute_abstract_op_node(cmd, self.server_list[0])

        self.list_of_procs = []

        # mount volume
        mount_dict = []
        self.mount = ("/mnt/replicated_mount", "/mnt/disperse_mount")
        for mount in self.mount:
            redant.execute_abstract_op_node(f"mkdir -p {mount}",
                                            self.client_list[0])
            mount_dict.append({
                "client": self.client_list[0],
                "mountpath": mount
            })

        self.counter = 1
        for mount_dir, volname in zip(self.mount, volnames):
            redant.volume_mount(self.server_list[0], volname, mount_dir,
                                self.client_list[0])

            # Run IO
            proc = redant.create_deep_dirs_with_files(mount_dir, self.counter,
                                                      2, 6, 3, 3,
                                                      self.client_list[0])

            self.list_of_procs.append(proc)
            self.counter += 10

        # Validate IO
        ret = redant.validate_io_procs(self.list_of_procs, mount_dict)
        if not ret:
            raise Exception("IO validation failed")

        # Add Brick to replicate Volume
        _, brick_cmd = redant.form_brick_cmd(self.server_list,
                                             self.brick_roots, replicate,
                                             3, True)
        redant.add_brick(replicate, brick_cmd, self.server_list[0],
                         force=True)

        # Trigger Rebalance on the volume
        redant.rebalance_start(replicate, self.server_list[0])

        # Add Brick to disperse Volume
        _, brick_cmd = redant.form_brick_cmd(self.server_list,
                                             self.brick_roots, disperse,
                                             6, True)
        redant.add_brick(disperse, brick_cmd, self.server_list[0],
                         force=True)

        # Trigger Rebalance on the volume
        redant.rebalance_start(disperse, self.server_list[0])

        # Check if Rebalance is completed on both the volume
        for volume in (replicate, disperse):
            ret = redant.wait_for_rebalance_to_complete(volume,
                                                        self.server_list[0],
                                                        timeout=600)
            if not ret:
                raise Exception(f"Rebalance is not completed on {volume}")
