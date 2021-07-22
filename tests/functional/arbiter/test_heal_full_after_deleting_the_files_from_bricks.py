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
    TC to check heal full after deleting files from bricks
"""

# disruptive;arb,dist-arb
# TODO NFS
from tests.d_parent_test import DParentTest


class TestArbiterSelfHeal(DParentTest):

    def run_test(self, redant):
        """
        - Create IO
        - Calculate arequal from mount
        - kill glusterd process and glustershd process on arbiter nodes
        - Delete data from backend from the arbiter nodes
        - Start glusterd process and force start the volume
          to bring the processes online
        - Check if heal is completed
        - Check for split-brain
        - Calculate arequal checksum and compare it
        """
        # Creating files on client side
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.proc_list = []
        counter = 0
        for mount in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount['mountpath'],
                                                      counter, 2, 2, 2, 10,
                                                      mount['client'])
            self.proc_list.append(proc)
            counter += 10

        if not redant.validate_io_procs(self.proc_list, self.mounts):
            raise Exception("IO validation failed")

        # Get arequal before killing gluster processes on arbiter node
        result_before_klng_procs = redant.collect_mounts_arequal(self.mounts)

        # Kill glusterd process and glustershd process on arbiter node
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if subvols:
            for subvol in subvols:
                arbiter = subvol[-1]
                node, brick_path = arbiter.split(':')
                # Stop glusterd
                redant.stop_glusterd(node)

                # Stop glustershd
                ret = redant.kill_process(node, "glustershd")
                if not ret:
                    if redant.is_shd_daemon_running(self.server_list[0], node,
                                                    self.vol_name):
                        raise Exception("The glustershd process is still "
                                        "running.")

        # Delete data from backend from the arbiter node
        for subvol in subvols:
            arbiter = subvol[-1]
            node, brick_path = arbiter.split(':')
            redant.execute_abstract_op_node(f"rm -rf {brick_path}/*", node)

        # Start glusterd process on each arbiter
        for subvol in subvols:
            arbiter = subvol[-1]
            node, brick_path = arbiter.split(':')
            redant.start_glusterd(node)

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal has not yet completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Heal is not yet complete")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequal after healing
        result_after_healing = redant.collect_mounts_arequal(self.mounts)

        # Comparing arequals before before killing arbiter processes
        # and after healing
        if result_before_klng_procs != result_after_healing:
            raise Exception("Arequals arequals before before killing arbiter"
                            "processes and after healing are not equal")
