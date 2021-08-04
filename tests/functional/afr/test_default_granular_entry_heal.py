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

 You should have received a copy of the GNU General Public License along`
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    TC to test default granular entry heal
"""

# disruptive;rep,dist-rep,arb,dist-arb
from random import choice
from tests.d_parent_test import DParentTest


class TestDefaultGranularEntryHeal(DParentTest):

    def _bring_bricks_offline(self):
        """Brings bricks offline and confirms if they are offline"""
        # Select bricks to bring offline from a replica set
        subvols = self.redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols of volume")

        self.bricks_to_bring_offline = []
        for subvol in subvols:
            self.bricks_to_bring_offline.append(choice(subvol))

        # Bring bricks offline
        if not self.redant.bring_bricks_offline(self.vol_name,
                                                self.bricks_to_bring_offline):
            raise Exception("Failed to bring bricks "
                            f"{self.bricks_to_bring_offline} offline")

        if not self.redant.are_bricks_offline(self.vol_name,
                                              self.bricks_to_bring_offline,
                                              self.server_list[0]):
            raise Exception(f"Bricks {self.bricks_to_bring_offline}"
                            " are not offline")

    def _restart_volume_and_bring_all_offline_bricks_online(self):
        """Restart volume and bring all offline bricks online"""

        if self.redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Heal is completed")

        if not (self.redant.bring_bricks_online(self.vol_name,
                self.server_list, self.bricks_to_bring_offline)):
            raise Exception("Failed to bring bricks "
                            f"{self.bricks_to_bring_offline} online")

        # Check if bricks are back online or not
        if not self.redant.are_bricks_online(self.vol_name,
                                             self.bricks_to_bring_offline,
                                             self.server_list[0]):
            raise Exception(f"Bricks: {self.bricks_to_bring_offline} not "
                            "online even after restart")

    def _wait_for_heal_to_completed(self):
        """Check if heal is completed"""
        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name,
                                                   timeout_period=3600):
            raise Exception("Heal is not yet completed")

    def _check_arequal_on_bricks_with_a_specific_arequal(self, arequal,
                                                         brick_list):
        """
        Compare an inital arequal checksum with bricks from a given brick list
        """
        init_val = arequal[0][-1].split(':')[-1]
        arequals = self.redant.collect_bricks_arequal(brick_list)
        for brick_arequal in arequals:
            brick_total = brick_arequal[-1].split(':')[-1]
            if init_val != brick_total:
                raise Exception("Arequals not matching")

    @staticmethod
    def _add_dir_path_to_brick_list(brick_list):
        """Add test_self_heal at the end of brick path"""
        dir_brick_list = []
        for brick in brick_list:
            dir_brick_list.append(f"{brick}/mydir")
        return dir_brick_list

    def _check_arequal_checksum_for_the_volume(self):
        """
        Check if arequals of mount point and bricks are
        are the same.
        """
        if self.volume_type == "rep" or self.volume_type == "arb":
            # Check arequals for "replicated"
            brick_list = self.redant.get_all_bricks(self.vol_name,
                                                    self.server_list[0])
            if brick_list is None:
                raise Exception("Failed to get the brick list")

            dir_brick_list = self._add_dir_path_to_brick_list(brick_list)

            # Get arequal before getting bricks offline
            work_dir = f"{self.mountpoint}/mydir"
            arequals = self.redant.collect_mounts_arequal(self.mounts,
                                                          work_dir)

            # Get arequal on bricks and compare with mount_point_total
            self._check_arequal_on_bricks_with_a_specific_arequal(
                arequals, dir_brick_list)

        # Check arequals for "distributed-replicated"
        if self.volume_type == "dist-rep" or self.volume_type == "dist-arb":
            # Get the subvolumes
            subvols = self.redant.get_subvols(self.vol_name,
                                              self.server_list[0])
            if not subvols:
                raise Exception("Failed to get the subvols of volume")
            num_subvols = len(subvols)

            # Get arequals and compare
            for i in range(0, num_subvols):
                # Get arequal for first brick
                brick_list = subvols[i]
                dir_brick_list = self._add_dir_path_to_brick_list(brick_list)
                arequals = (self.redant.collect_bricks_arequal(
                            dir_brick_list[0]))

                # Get arequal for every brick and compare with first brick
                self._check_arequal_on_bricks_with_a_specific_arequal(
                    arequals, dir_brick_list)

    def run_test(self, redant):
        """
        Test case:
        1. Create a cluster.
        2. Create volume start it and mount it.
        3. Check if cluster.granular-entry-heal is ON by default or not.
        4. Check /var/lib/glusterd/<volname>/info for
           cluster.granular-entry-heal=on.
        5. Check if option granular-entry-heal is present in the
           volume graph or not.
        6. Kill one or two bricks of the volume depending on volume type.
        7. Create all types of files on the volume like text files, hidden
           files, link files, dirs, char device, block device and so on.
        8. Bring back the killed brick by restarting the volume.
        9. Wait for heal to complete.
        10. Check arequal-checksum of all the bricks and see if it's proper
            or not.
        """
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        # Check if cluster.granular-entry-heal is ON by default or not
        ret = redant.get_volume_options(self.vol_name, 'granular-entry-heal',
                                        self.server_list[0])
        if ret['cluster.granular-entry-heal'] != "on":
            raise Exception("Value of cluster.granular-entry-heal not on "
                            "by default")

        # Check var/lib/glusterd/<volname>/info for
        # cluster.granular-entry-heal=on
        ret = (redant.occurences_of_pattern_in_file(
               self.server_list[0], "cluster.granular-entry-heal=on",
               f"/var/lib/glusterd/vols/{self.vol_name}/info"))
        if ret != 1:
            raise Exception("Failed get cluster.granular-entry-heal=on in"
                            " info file")

        # Check if option granular-entry-heal is present in the
        # volume graph or not
        ret = (redant.occurences_of_pattern_in_file(
               self.client_list[0], "option granular-entry-heal on",
               f"/var/log/glusterfs/mnt-{self.vol_name}.log"))
        if ret < 1:
            raise Exception("Failed to find granular-entry-heal in volume"
                            " graph")

        # Kill one or two bricks of the volume depending on volume type
        self._bring_bricks_offline()

        # Create all types of files on the volume like text files, hidden
        # files, link files, dirs, char device, block device and so on
        cmd = (f"cd {self.mountpoint}; mkdir mydir; cd mydir; mkdir dir; "
               "mkdir .hiddendir; touch file; touch .hiddenfile; "
               "mknod blockfile b 1 5; mknod charfile b 1 5; mkfifo pipefile;"
               " touch fileforhardlink; touch fileforsoftlink; "
               "ln fileforhardlink hardlinkfile; ln -s fileforsoftlink "
               "softlinkfile")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Bring back the killed brick by restarting the volume	Bricks should
        # be online again
        self._restart_volume_and_bring_all_offline_bricks_online()

        # Wait for heal to complete
        self._wait_for_heal_to_completed()

        # Check arequal-checksum of all the bricks and see if it's proper or
        # not
        self._check_arequal_checksum_for_the_volume()
