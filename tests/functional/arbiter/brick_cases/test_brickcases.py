"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check arbiter specific brick cases
"""

# disruptive;
# TODO: NFS, CIFS
import traceback
from tests.d_parent_test import DParentTest


class TestGlusterArbiterVolumeTypeChangeClass(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails early
        """
        try:
            if not self.io_validation_complete:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mount_dict)):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        - Change the volume type from replicated to arbiter
        - Perform add-brick, rebalance on arbitered volume
        - Perform replace-brick on arbitered volume
        - Perform remove-brick on arbitered volume
        """
        # Perform the below test for replica 2, distributed replica 2 volumes
        for i in range(1, 3):
            self.io_validation_complete = True

            # Create and start a volume
            conf_hash = {
                "dist_count": i,
                "replica_count": 2,
                "transport": "tcp"
            }
            vol_type = "rep" if i == 1 else "dist-rep"
            self.volname = f"{self.test_name}-{vol_type}"
            redant.setup_volume(self.volname, self.server_list[0],
                                conf_hash, self.server_list,
                                self.brick_roots, force=True)
            self.mountpoint = f"/mnt/{self.volname}"
            redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                            self.client_list[0])

            # Start IO on mounts
            self.mount_dict = {
                "client": self.client_list[0],
                "mountpath": self.mountpoint
            }
            proc = redant.create_deep_dirs_with_files(self.mountpoint, 1, 1,
                                                      1, 1, 5,
                                                      self.client_list[0])

            # Validate IO
            ret = redant.validate_io_procs(proc, self.mount_dict)
            if not ret:
                raise Exception("IO validation failed")

            # Adding bricks to make an Arbiter Volume
            force = False
            if len(self.server_list) < 6:
                force = True

            kwargs = {'replica_count': 1, 'arbiter_count': 1}
            ret = redant.expand_volume(self.server_list[0], self.volname,
                                       self.server_list, self.brick_roots,
                                       force, **kwargs)
            if not ret:
                raise Exception(f"Failed to expand the volume {self.volname}")

            # Verifying all bricks online
            if not (redant.verify_all_process_of_volume_are_online(
                    self.volname, self.server_list[0])):
                raise Exception("All process of volume are not online")

            # Checking for heals to finish after changing the volume type
            # from replicated to arbitered volume
            if not redant.monitor_heal_completion(self.server_list[0],
                                                  self.volname):
                raise Exception("Heal has not yet completed")

            # Check if heal is completed
            if not redant.is_heal_complete(self.server_list[0], self.volname):
                raise Exception("Heal is not yet complete")

            # Start IO on mounts
            self.all_mounts_procs = []
            proc = redant.create_deep_dirs_with_files(self.mountpoint, 5, 1,
                                                      1, 1, 5,
                                                      self.client_list[0])
            self.all_mounts_procs.append(proc)
            self.io_validation_complete = False

            # Start add-brick (subvolume-increase)
            ret = redant.expand_volume(self.server_list[0], self.volname,
                                       self.server_list, self.brick_roots)
            if not ret:
                raise Exception("Failed to expand the volume when IO in "
                                f"progress on volume {self.volname}")

            # Verify volume's all process are online
            if not (redant.verify_all_process_of_volume_are_online(
                    self.volname, self.server_list[0])):
                raise Exception("All process of volume are not online")

            # Start Rebalance
            redant.rebalance_start(self.volname, self.server_list[0])

            # Log Rebalance status
            redant.get_rebalance_status(self.volname, self.server_list[0])

            # Wait for rebalance to complete
            if not redant.wait_for_rebalance_to_complete(self.volname,
                                                         self.server_list[0],
                                                         600):
                raise Exception("Rebalance did not complete "
                                "despite waiting for 10 mins")

            # Replace brick from a sub-volume
            ret = (redant.replace_brick_from_volume(self.volname,
                   self.server_list[0], self.server_list,
                   brick_roots=self.brick_roots))
            if not ret:
                raise Exception("Failed to replace faulty brick from volume")

            # Wait for volume processes to be online
            if not (redant.wait_for_volume_process_to_be_online(self.volname,
                    self.server_list[0], self.server_list)):
                raise Exception("Failed to wait for volume processes to "
                                "be online")

            # Verify volume's all process are online
            if not (redant.verify_all_process_of_volume_are_online(
                    self.volname, self.server_list[0])):
                raise Exception("All process of volume are not online")

            # Wait for self-heal to complete
            if not redant.monitor_heal_completion(self.server_list[0],
                                                  self.volname):
                raise Exception("Heal has not yet completed")

            # Check if heal is completed
            if not redant.is_heal_complete(self.server_list[0], self.volname):
                raise Exception("Heal is not yet complete")

            # Shrinking volume by removing bricks from volume when IO
            # is in progress
            ret = redant.shrink_volume(self.server_list[0], self.volname,
                                       rebal_timeout=900)
            if not ret:
                raise Exception("Failed to shrink the volume when IO in "
                                f"progress on volume {self.volname}")

            # Verify volume's all process are online
            if not (redant.verify_all_process_of_volume_are_online(
                    self.volname, self.server_list[0])):
                raise Exception("All process of volume are not online")

            # Validate IO
            ret = redant.validate_io_procs(self.all_mounts_procs,
                                           self.mount_dict)
            if not ret:
                raise Exception("IO validation failed")
            self.io_validation_complete = True
