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
    TC to check self-heal on replace brick while IO is in progress
"""

# disruptive;rep,dist-rep
# TODO: NFS, CIFS

import traceback
from tests.d_parent_test import DParentTest


class TestAFRSelfHeal(DParentTest):

    def terminate(self):
        try:
            if not self.io_validation_complete:
                if not (self.redant.wait_for_io_to_complete(self.procs_list,
                                                            self.mounts)):
                    raise Exception("IO failed on some of the clients")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        - Create directory on mount point and write files/dirs
        - Create another set of files (1K files)
        - While creation of files/dirs are in progress Kill one brick
        - Remove the contents of the killed brick(simulating disk replacement)
        - When the IO's are still in progress, restart glusterd on the nodes
          where we simulated disk replacement to bring back bricks online
        - Start volume heal
        - Wait for IO's to complete
        - Verify whether the files are self-healed
        - Calculate arequals of the mount point and all the bricks
        """
        self.io_validation_complete = True
        # Create dirs with files
        command = ("python3 /tmp/file_dir_ops.py create_deep_dirs_with_files "
                   f"-d 2 -l 2 -n 2 -f 10 {self.mountpoint}")
        redant.execute_abstract_op_node(command, self.client_list[0])

        # Creating another set of files (1K files)
        self.procs_list = []

        # Create dirs with files
        proc = redant.create_files("10k", self.mountpoint,
                                   self.client_list[0], 1500)
        self.procs_list.append(proc)
        self.io_validation_complete = False
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Validate IO
        ret = redant.validate_io_procs(self.procs_list, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")
        self.io_validation_complete = True

        # Select bricks to bring offline
        bricks_to_bring_offline = \
            redant.select_volume_bricks_to_bring_offline(self.vol_name,
                                                         self.server_list[0])

        # Bring brick offline
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} are not "
                            "offline")

        # Remove the content of the killed bricks
        for brick in bricks_to_bring_offline:
            brick_node, brick_path = brick.split(':')

            # Removing files
            cmd = f"cd {brick_path}; rm -rf *"
            redant.execute_abstract_op_node(cmd, brick_node)

        # Bring brick online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          bricks_to_bring_offline):
            raise Exception("Failed to bring bricks "
                            f"{bricks_to_bring_offline} online")

        # Wait for volume processes to be online
        if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                self.server_list[0], self.server_list)):
            raise Exception("Failed to wait for volume processes to "
                            "be online")

        # Verify volume's all process are online
        if not (redant.verify_all_process_of_volume_are_online(self.vol_name,
                self.server_list[0])):
            raise Exception("All process of volume are not online")

        # Wait for self-heal-daemons to be online
        if not redant.is_shd_daemonized(self.server_list):
            raise Exception("Either No self heal daemon process found, "
                            "or more than one process found")

        # Start healing
        if not redant.trigger_heal_full(self.vol_name, self.server_list[0]):
            raise Exception("Heal is not started")

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Heal is not yet complete")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Check arequals for "replicated"
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if self.volume_type == "rep":
            # Get arequal after bricks are online
            arequals = redant.collect_mounts_arequal(self.mounts)
            mount_point_total = arequals[0][-1].split(':')[-1]

            # Get arequal on bricks and compare with mount_point_total
            arequals = redant.collect_bricks_arequal(all_bricks)
            for arequal in arequals:
                brick_total = arequal[-1].split(':')[-1]
                if mount_point_total != brick_total:
                    raise Exception("Arequals for mountpoint and brick are"
                                    " not equal")
        else:
            # Get the subvolumes
            subvols = redant.get_subvols(self.vol_name, self.server_list[0])

            # Get arequals and compare
            for i in range(0, len(subvols)):

                # Get arequal for first brick
                arequal = redant.collect_bricks_arequal(subvols[i][0])
                first_brick_total = arequal[0][-1].split(':')[-1]

                # Get arequal for every brick and compare with first brick
                arequals = redant.collect_bricks_arequal(subvols[i])
                for arequal in arequals:
                    brick_total = arequal[-1].split(':')[-1]
                    if first_brick_total != brick_total:
                        raise Exception("Arequals for subvol and brick are "
                                        "not equal")
