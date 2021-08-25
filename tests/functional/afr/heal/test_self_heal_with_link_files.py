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

# disruptive;dist-rep,rep
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def _create_files_and_dirs_on_mount_point(self, second_attempt=False):
        """A function to create files and dirs on mount point"""
        # Create a parent directory test_link_self_heal on mount point
        if not second_attempt:
            self.redant.create_dir(self.mountpoint,
                                   'test_link_self_heal',
                                   self.client_list[0])

        # Create dirctories and files inside directory test_link_self_heal
        io_cmd = (f"cd {self.mountpoint}/test_link_self_heal;"
                  "for i in `seq 1 5`; do mkdir dir.$i; "
                  "for j in `seq 1 10`; do dd if=/dev/random "
                  "of=dir.$i/file.$j bs=1k count=$j; done; done")
        if second_attempt:
            io_cmd = (f"cd {self.mountpoint}/test_link_self_heal;"
                      "for i in `seq 1 5` ; do for j in `seq 1 10`; "
                      "do dd if=/dev/random "
                      "of=sym_link_dir.$i/new_file.$j bs=1k count=$j;"
                      " done; done ")
        self.redant.execute_abstract_op_node(io_cmd,
                                             self.client_list[0])

    def _create_soft_links_to_directories(self):
        """Create soft links to directories"""
        cmd = (f"cd {self.mountpoint}/test_link_self_heal;"
               "for i in `seq 1 5`; do ln -s dir.$i sym_link_dir.$i;"
               " done")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _verify_soft_links_to_dir(self, option=0):
        """Verify soft links to dir"""
        cmd_list = [
            ("for i in `seq 1 5`; do stat -c %F sym_link_dir.$i | "
             "grep -F 'symbolic link'; if [ $? -ne 0 ]; then exit 1;"
             " fi ; done; for i in `seq 1 5` ; do readlink sym_link_dir.$i | "
             "grep \"dir.$i\"; if [ $? -ne 0 ]; then exit 1; fi; done; "),
            ("for i in `seq 1 5`; do for j in `seq 1 10`; do ls "
             "dir.$i/new_file.$j; if [ $? -ne 0 ]; then exit 1; fi; done; "
             "done")]

        # Generate command to check according to option
        if option == 2:
            verify_cmd = "".join(cmd_list)
        else:
            verify_cmd = cmd_list[option]

        cmd = (f"cd {self.mountpoint}/test_link_self_heal;{verify_cmd}")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _create_hard_links_to_files(self, second_attempt=False):
        """Create hard links to files"""
        io_cmd = ("for i in `seq 1 5`;do for j in `seq 1 10`;"
                  "do ln dir.$i/file.$j dir.$i/link_file.$j;done; done")
        if second_attempt:
            io_cmd = ("for i in `seq 1 5`; do mkdir new_dir.$i; "
                      "for j in `seq 1 10`; do ln dir.$i/file.$j "
                      "new_dir.$i/new_file.$j;done; done;")

        cmd = (f"cd {self.mountpoint}/test_link_self_heal; {io_cmd}")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _verify_hard_links_to_files(self, second_set=False):
        """Verify if hard links to files"""
        file_to_compare = "dir.$i/link_file.$j"
        if second_set:
            file_to_compare = "new_dir.$i/new_file.$j"

        cmd = (f"cd {self.mountpoint}/test_link_self_heal;"
               "for i in `seq 1 5`; do for j in `seq 1 10`;"
               "do if [ `stat -c %i dir.$i/file.$j` -ne `stat -c %i "
               f"{file_to_compare}` ];then exit 1; fi; done; done")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _bring_bricks_offline(self):
        """Brings bricks offline and confirms if they are offline"""
        # Select bricks to bring offline from a replica set
        subvols = self.redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols of volume")

        self.bricks_to_bring_offline = []
        for subvol in subvols:
            self.bricks_to_bring_offline.append(subvol[0])

        # Bring bricks offline
        self.redant.bring_bricks_offline(self.vol_name,
                                         self.bricks_to_bring_offline)
        if not (self.redant.
                are_bricks_offline(self.vol_name, self.bricks_to_bring_offline,
                                   self.server_list[0])):
            raise Exception(f"Bricks {self.bricks_to_bring_offline} are"
                            "not offline.")

    def _restart_volume_and_bring_all_offline_bricks_online(self):
        """Restart volume and bring all offline bricks online"""
        self.redant.bring_bricks_online(self.vol_name, self.server_list,
                                        self.bricks_to_bring_offline)

        # Check if bricks are back online or not
        if not (self.redant.
                are_bricks_online(self.vol_name,
                                  self.bricks_to_bring_offline,
                                  self.server_list[0])):
            raise Exception(f"Bricks {self.bricks_to_bring_offline} are "
                            "not online.")

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
            dir_brick_list.append(f"{brick}/test_link_self_heal")
        return dir_brick_list

    def _check_arequal_checksum_for_the_volume(self):
        """
        Check if arequals of mount point and bricks are
        are the same.
        """
        if self.volume_type == "rep":
            # Check arequals for "replicated"
            brick_list = self.redant.get_all_bricks(self.vol_name,
                                                    self.server_list[0])
            if brick_list is None:
                raise Exception("Failed to get the brick list")
            dir_brick_list = self._add_dir_path_to_brick_list(brick_list)

            # Get arequal before getting bricks offline
            work_dir = f'{self.mountpoint}/test_link_self_heal'
            arequals = self.redant.collect_mounts_arequal(self.mounts,
                                                          work_dir)

            # Get arequal on bricks and compare with mount_point_total
            self._check_arequal_on_bricks_with_a_specific_arequal(
                arequals, dir_brick_list)

        # Check arequals for "distributed-replicated"
        else:
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

    def _check_heal_is_completed_and_not_in_split_brain(self):
        """Check if heal is completed and volume not in split brain"""
        # Check if heal is completed
        if not self.redant.is_heal_complete(self.server_list[0],
                                            self.vol_name):
            raise Exception("Heal is not completed")

        # Check if volume is in split brian or not
        if self.redant.is_volume_in_split_brain(self.server_list[0],
                                                self.vol_name):
            raise Exception("Volume is in split-brain state")

    def _check_if_there_are_files_and_dirs_to_be_healed(self):
        """Check if there are files and dirs to be healed"""
        if self.redant.is_heal_complete(self.server_list[0],
                                        self.vol_name):
            raise Exception("Heal is completed")

    def _wait_for_heal_is_completed(self):
        """Check if heal is completed"""
        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name, 3600):
            raise Exception("Heal has not yet completed")

    def _replace_one_random_brick(self):
        """Replace one random brick from the volume"""
        ret = (self.redant.replace_brick_from_volume(self.vol_name,
               self.server_list[0], self.server_list,
               brick_roots=self.brick_roots))
        if not ret:
            raise Exception("Failed to replace faulty brick from"
                            " volume")

    def _test_self_heal_of_hard_links(self):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create a directory and create files and directories inside it
           on mount point.
        3. Collect and compare arequal-checksum according to the volume type
           for bricks.
        4. Bring down brick processes accoding to the volume type.
        5. Create hard links for the files created in step 2.
        6. Check if heal info is showing all the files and dirs to be healed.
        7. Bring brack all brick processes which were killed.
        8. Wait for heal to complete on the volume.
        9. Check if heal is complete and check if volume is in split brain.
        10. Collect and compare arequal-checksum according to the volume type
            for bricks.
        11. Verify if hard links are proper or not.
        12. Do a lookup on mount point.
        13. Bring down brick processes accoding to the volume type.
        14. Create a second set of hard links to the files.
        15. Check if heal info is showing all the files and dirs to be healed.
        16. Bring brack all brick processes which were killed.
        17. Wait for heal to complete on the volume.
        18. Check if heal is complete and check if volume is in split brain.
        19. Collect and compare arequal-checksum according to the volume type
            for bricks.
        20. Verify both set of hard links are proper or not.
        21. Do a lookup on mount point.
        22. Pick a random brick and replace it.
        23. Wait for heal to complete on the volume.
        24. Check if heal is complete and check if volume is in split brain.
        25. Collect and compare arequal-checksum according to the volume type
            for bricks.
        26. Verify both set of hard links are proper or not.
        27. Do a lookup on mount point.
        """
        # Create a directory and create files and directories inside it
        # on mount point
        self._create_files_and_dirs_on_mount_point()

        # Collect and compare arequal-checksum according to the volume type
        # for bricks
        self._check_arequal_checksum_for_the_volume()

        for attempt in (False, True):

            # Bring down brick processes accoding to the volume type
            self._bring_bricks_offline()

            # Create hardlinks for the files created in step 2
            self._create_hard_links_to_files(second_attempt=attempt)

            # Check if heal info is showing all the files and dirs to
            # be healed
            self._check_if_there_are_files_and_dirs_to_be_healed()

            # Bring back all brick processes which were killed
            self._restart_volume_and_bring_all_offline_bricks_online()

            # Wait for heal to complete on the volume
            self._wait_for_heal_is_completed()

            # Check if heal is complete and check if volume is in split brain
            self._check_heal_is_completed_and_not_in_split_brain()

            # Collect and compare arequal-checksum according to the volume
            # type for bricks
            self._check_arequal_checksum_for_the_volume()

            # Verify if hard links are proper or not
            self._verify_hard_links_to_files()
            if attempt:
                self._verify_hard_links_to_files(second_set=attempt)

        # Pick a random brick and replace it
        self._replace_one_random_brick()

        # Wait for heal to complete on the volume
        self._wait_for_heal_is_completed()

        # Check if heal is complete and check if volume is in split brain
        self._check_heal_is_completed_and_not_in_split_brain()

        # Collect and compare arequal-checksum according to the volume
        # type for bricks
        self._check_arequal_checksum_for_the_volume()

        # Verify if hard links are proper or not
        self._verify_hard_links_to_files()
        self._verify_hard_links_to_files(second_set=True)

    def _test_self_heal_of_soft_links(self):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create a directory and create files and directories inside it
           on mount point.
        3. Collect and compare arequal-checksum according to the volume type
           for bricks.
        4. Bring down brick processes accoding to the volume type.
        5. Create soft links for the dirs created in step 2.
        6. Verify if soft links are proper or not.
        7. Add files through the soft links.
        8. Verify if the soft links are proper or not.
        9. Check if heal info is showing all the files and dirs to be healed.
        10. Bring brack all brick processes which were killed.
        11. Wait for heal to complete on the volume.
        12. Check if heal is complete and check if volume is in split brain.
        13. Collect and compare arequal-checksum according to the volume type
            for bricks.
        14. Verify if soft links are proper or not.
        15. Do a lookup on mount point.
        """
        # Create a directory and create files and directories inside it
        # on mount point
        self._create_files_and_dirs_on_mount_point()

        # Collect and compare arequal-checksum according to the volume type
        # for bricks
        self._check_arequal_checksum_for_the_volume()

        # Bring down brick processes accoding to the volume type
        self._bring_bricks_offline()

        # Create soft links for the dirs created in step 2
        self._create_soft_links_to_directories()

        # Verify if soft links are proper or not
        self._verify_soft_links_to_dir()

        # Add files through the soft links
        self._create_files_and_dirs_on_mount_point(second_attempt=True)

        # Verify if the soft links are proper or not
        self._verify_soft_links_to_dir(option=1)

        # Check if heal info is showing all the files and dirs to
        # be healed
        self._check_if_there_are_files_and_dirs_to_be_healed()

        # Bring back all brick processes which were killed
        self._restart_volume_and_bring_all_offline_bricks_online()

        # Wait for heal to complete on the volume
        self._wait_for_heal_is_completed()

        # Check if heal is complete and check if volume is in split brain
        self._check_heal_is_completed_and_not_in_split_brain()

        # Verify if soft links are proper or not
        self._verify_soft_links_to_dir(option=2)

    def run_test(self, redant):
        """
        1.Test case for selfheal on hard links
        2.Test case for selfheal on soft links
        """
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }

        self._test_self_heal_of_hard_links()
        redant.logger.info("Test Case for selfheal on hard links "
                           "is successful")
        self._test_self_heal_of_soft_links()
        redant.logger.info("Test Case for selfheal on soft links "
                           "is successful")
