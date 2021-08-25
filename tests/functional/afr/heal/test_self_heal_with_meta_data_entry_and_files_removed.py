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

Description
    Add tests to check self heal
"""

# disruptive;dist-rep,rep
import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        # Delete non-root users and group if created
        try:
            if self.user_group_created:
                # Delete non-root users
                for user in self.users:
                    if not self.redant.del_user(self.client_list[0],
                                                user):
                        raise Exception(f"Unable to delete user {user}"
                                        f"on {self.client_list[0]}")

                # Delete non-root group
                if not self.redant.group_del(self.client_list[0],
                                             'qa_all'):
                    raise Exception(f"Unable to delete group 'qa_all'"
                                    f"on {self.client_list[0]}")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _setup_user(self):
        # Create non-root group
        if not self.redant.group_add(self.client_list[0], 'qa_all'):
            raise Exception("Failed to create group qa_all")

        # Create non-root users
        self.users = ('qa_func', 'qa_system', 'qa_perf')
        for user in self.users:
            if not self.redant.add_user(self.client_list[0], user,
                                        group='qa_all'):
                raise Exception(f"Failed to create user {user}")
            self.user_group_created = True

    def _set_granular_heal_to_on_or_off(self, enabled=False):
        """Set granular heal to ON or OFF"""
        granular = self.redant.get_volume_options(self.vol_name,
                                                  'granular-entry-heal',
                                                  self.server_list[0])
        if enabled:
            if granular['cluster.granular-entry-heal'] != 'on':
                if not (self.redant.enable_granular_heal(
                        self.vol_name, self.server_list[0])):
                    raise Exception("Failed to enable "
                                    "granular-entry-heal")
        else:
            if granular['cluster.granular-entry-heal'] == 'on':
                if not (self.redant.disable_granular_heal(
                        self.vol_name, self.server_list[0])):
                    raise Exception("Failed to disable "
                                    "granular-entry-heal")

    def _run_cmd(self, io_cmd, err_msg):
        """Run cmd and show error message if it fails"""
        cmd = (f"cd {self.mountpoint}/test_self_heal; {io_cmd}")
        ret = self.redant.execute_abstract_op_node(cmd,
                                                   self.client_list[0])
        if ret['error_code'] != 0:
            raise Exception(f"Command failed with error - {err_msg}")

    def _create_files_and_dirs_on_mount_point(self, index, second_set=False):
        """A function to create files and dirs on mount point"""
        # Create a parent directory test_self_heal on mount point
        if not second_set:
            self.redant.create_dir(self.mountpoint, 'test_self_heal',
                                   self.client_list[0])

        # Create dirctories and files inside directory test_self_heal
        io_cmd = ("for i in `seq 1 50`; do mkdir dir.$i; dd if=/dev/random"
                  " of=file.$i count=1K bs=$i; done",

                  "for i in `seq 1 100`; do mkdir dir.$i; for j in `seq 1 5`;"
                  " do dd if=/dev/random of=dir.$i/file.$j bs=1K count=$j"
                  ";done;done",

                  "for i in `seq 1 10`; do mkdir l1_dir.$i; for j in `seq "
                  "1 5`; do mkdir l1_dir.$i/l2_dir.$j; for k in `seq 1 10`;"
                  " do dd if=/dev/random of=l1_dir.$i/l2_dir.$j/test.$k"
                  " bs=1k count=$k; done; done; done;",

                  "for i in `seq 51 100`; do mkdir new_dir.$i; for j in `seq"
                  " 1 10`; do dd if=/dev/random of=new_dir.$i/new_file.$j "
                  "bs=1K count=$j; done; dd if=/dev/random of=new_file.$i"
                  " count=1K bs=$i; done ;")

        self._run_cmd(io_cmd[index], "Failed to create dirs and files inside")

    def _delete_files_and_dirs(self):
        """Delete files and dirs from mount point"""
        io_cmd = ("for i in `seq 1 50`; do rm -rf dir.$i; rm -f file.$i;done")
        self._run_cmd(io_cmd, "Failed to delete dirs and files")

    def _rename_files_and_dirs(self):
        """Rename files and dirs from mount point"""
        io_cmd = ("for i in `seq 51 100`;"
                  "do mv new_file.$i renamed_file.$i;"
                  "for j in `seq 1 10`;"
                  "do mv new_dir.$i/new_file.$j"
                  "new_dir.$i/renamed_file.$j ; done ;"
                  "mv new_dir.$i renamed_dir.$i; done;")
        self._run_cmd(io_cmd, "Failed to rename dirs and files")

    def _change_meta_deta_of_dirs_and_files(self):
        """Change meta data of dirs and files"""
        cmds = (
            # Change permission
            "for i in `seq 1 100`; do chmod 555 dir.$i; done; "
            "for i in `seq 1 50`; do for j in `seq 1 5`; do chmod 666 "
            "dir.$i/file.$j; done; done; for i in `seq 51 100`; do for "
            "j in `seq 1 5`;do chmod 444 dir.$i/file.$j; done; done;",

            # Change ownership
            "for i in `seq 1 35`; do chown -R qa_func dir.$i; done; "
            "for i in `seq 36 70`; do chown -R qa_system dir.$i; done; "
            "for i in `seq 71 100`; do chown -R qa_perf dir.$i; done;",

            # Change group
            "for i in `seq 1 100`; do chgrp -R qa_all dir.$i; done;")

        for io_cmd in cmds:
            self._run_cmd(io_cmd,
                          "Failed to change meta data on dirs and files")

    def _verify_meta_data_of_files_and_dirs(self):
        cmds = (
            # Verify permissions
            "for i in `seq 1 50`; do stat -c %a dir.$i | grep -F \"555\";"
            " if [ $? -ne 0 ]; then exit 1; fi; for j in `seq 1 5` ; do "
            "stat -c %a dir.$i/file.$j | grep -F \"666\"; if [ $? -ne 0 ]"
            ";  then exit 1; fi; done; done; for i in `seq 51 100`; do "
            "stat -c %a dir.$i | grep -F \"555\";if [ $? -ne 0 ]; then "
            "exit 1; fi; for j in `seq 1 5`; do stat -c %a dir.$i/file.$j"
            " | grep -F \"444\"; if [ $? -ne 0 ]; then exit 1; fi; done;"
            "done;",

            # Verify ownership
            "for i in `seq 1 35`; do stat -c %U dir.$i | grep -F "
            "\"qa_func\"; if [ $? -ne 0 ]; then exit 1; fi; for j in "
            "`seq 1 5`; do stat -c %U dir.$i/file.$j | grep -F "
            "\"qa_func\"; if [ $? -ne 0 ]; then exit 1; fi; done; done;"
            " for i in `seq 36 70` ; do stat -c %U dir.$i | grep -F "
            "\"qa_system\"; if [ $? -ne 0 ]; then exit 1; fi; for j in "
            "`seq 1 5`; do stat -c %U dir.$i/file.$j | grep -F "
            "\"qa_system\"; if [ $? -ne 0 ]; then exit 1; fi; done; done;"
            " for i in `seq 71 100` ; do stat -c %U dir.$i | grep -F "
            "\"qa_perf\"; if [ $? -ne 0 ]; then exit 1; fi; for j in "
            "`seq 1 5`; do stat -c %U dir.$i/file.$j | grep -F "
            "\"qa_perf\"; if [ $? -ne 0 ]; then exit 1; fi; done; done;",

            # Verify group
            "for i in `seq 1 100`; do stat -c %G dir.$i | grep -F "
            "\"qa_all\"; if [ $? -ne 0 ]; then exit 1; fi; for j in "
            "`seq 1 5`; do stat -c %G dir.$i/file.$j | grep -F "
            "\"qa_all\"; if [ $? -ne 0 ]; then exit 1; fi; done; done;")

        for io_cmd in cmds:
            self._run_cmd(io_cmd, "Meta data of dirs and files not proper")

    def _set_and_remove_extended_attributes(self, remove=False):
        """Set and remove extended attributes"""
        # Command to set extended attribute to files and dirs
        io_cmd = ("for i in `seq 1 100`; do setfattr -n trusted.name -v "
                  "testing_xattr_selfheal_on_dirs dir.$i; for j in `seq 1 "
                  "5`;do setfattr -n trusted.name -v "
                  "testing_xattr_selfheal_on_files dir.$i/file.$j; done; "
                  "done;")
        err_msg = "Failed to set extended attributes to files and dirs"

        if remove:
            # Command to remove extended attribute set on files and dirs
            io_cmd = ("for i in `seq 1 100`; do setfattr -x trusted.name "
                      "dir.$i; for j in `seq 1 5`; do setfattr -x "
                      "trusted.name dir.$i/file.$j ; done ; done ;")
            err_msg = "Failed to remove extended attributes to files and dirs"

        self._run_cmd(io_cmd, err_msg)

    def _verify_if_extended_attributes_are_proper(self, remove=False):
        """Verify if extended attributes are set or remove properly"""
        io_cmd = ("for i in `seq 1 100`; do getfattr -n trusted.name -e text "
                  "dir.$i | grep -F 'testing_xattr_selfheal_on_dirs'; if [ $? "
                  "-ne 0 ]; then exit 1 ; fi ; for j in `seq 1 5` ; do "
                  "getfattr -n trusted.name -e text dir.$i/file.$j | grep -F "
                  "'testing_xattr_selfheal_on_files'; if [ $? -ne 0 ]; then "
                  "exit 1; fi; done; done;")
        err_msg = "Extended attributes on files and dirs are not proper"
        if remove:
            io_cmd = ("for i in `seq 1 100`; do getfattr -n trusted.name -e "
                      "text dir.$i; if [ $? -eq 0 ]; then exit 1; fi; for j in"
                      " `seq 1 5`; do getfattr -n trusted.name -e text "
                      "dir.$i/file.$j; if [ $? -eq 0]; then exit 1; fi; done; "
                      "done;")
            err_msg = "Extended attributes set to files and dirs not removed"
        self._run_cmd(io_cmd, err_msg)

    def _remove_files_and_create_dirs_with_the_same_name(self):
        """Remove files and create dirs with the same name"""
        io_cmd = ("for i in `seq 1 10`; do for j in `seq 1 5`; do for k in "
                  "`seq 1 10`; do rm -f l1_dir.$i/l2_dir.$j/test.$k; mkdir "
                  "l1_dir.$i/l2_dir.$j/test.$k; done; done; done;")
        self._run_cmd(io_cmd,
                      "Failed to remove files and create dirs with same name")

    def _verify_if_dirs_are_proper_or_not(self):
        """Verify if dirs are proper or not"""
        io_cmd = ("for i in `seq 1 10`; do for j in `seq 1 5`; do for k in "
                  "`seq 1 10`; do stat -c %F l1_dir.$i/l2_dir.$j/test.$k | "
                  "grep -F 'directory'; if [ $? -ne 0 ]; then exit 1; fi; "
                  "done; done; done;")
        self._run_cmd(io_cmd, "Dirs created instead of files aren't proper")

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
            dir_brick_list.append(f"{brick}/test_self_heal")
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
            work_dir = f'{self.mountpoint}/test_self_heal'
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

    def _check_heal_status_restart_vol_wait_and_check_data(self):
        """
        Perform repeatative steps mentioned below:
        1 Check if heal info is showing all the files and dirs to be healed
        2 Bring back all brick processes which were killed
        3 Wait for heal to complete on the volume
        4 Check if heal is complete and check if volume is in split brain
        5 Collect and compare arequal-checksum according to the volume type
          for bricks
        """
        # Check if heal info is showing all the files and dirs to be healed
        self._check_if_there_are_files_and_dirs_to_be_healed()

        # Bring back all brick processes which were killed
        self._restart_volume_and_bring_all_offline_bricks_online()

        # Wait for heal to complete on the volume
        self._wait_for_heal_is_completed()

        # Check if heal is complete and check if volume is in split brain
        self._check_heal_is_completed_and_not_in_split_brain()

        # Collect and compare arequal-checksum according to the volume type
        # for bricks
        self._check_arequal_checksum_for_the_volume()

    def _run_test_self_heal_entry_heal(self):
        """Run steps of test_self_heal_entry_heal"""
        # Create a directory and create files and directories inside it on
        # mount point
        self._create_files_and_dirs_on_mount_point(0)

        # Collect and compare arequal-checksum according to the volume type
        # for bricks
        self._check_arequal_checksum_for_the_volume()

        # Bring down brick processes accoding to the volume type
        self._bring_bricks_offline()

        # Create a new set of files and directories on mount point
        self._create_files_and_dirs_on_mount_point(3, second_set=True)

        self._check_heal_status_restart_vol_wait_and_check_data()

        # Bring down brick processes accoding to the volume type
        self._bring_bricks_offline()

        # Delete files and directories from mount point
        self._delete_files_and_dirs()

        self._check_heal_status_restart_vol_wait_and_check_data()

        # Bring down brick processes accoding to the volume type
        self._bring_bricks_offline()

        # Rename the existing files and dirs
        self._rename_files_and_dirs()

        self._check_heal_status_restart_vol_wait_and_check_data()

    def _test_self_heal_entry_heal(self):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create a directory and create files and directories inside it
           on mount point.
        3. Collect and compare arequal-checksum according to the volume type
           for bricks.
        4. Bring down brick processes accoding to the volume type.
        5. Create a new set of files and directories on mount point.
        6. Check if heal info is showing all the files and dirs to be healed.
        7. Bring back all brick processes which were killed.
        8. Wait for heal to complete on the volume.
        9. Check if heal is complete and check if volume is in split brain.
        10. Collect and compare arequal-checksum according to the volume type
            for bricks.
        11. Bring down brick processes accoding to the volume type.
        12. Delete files and directories from mount point.
        13. Check if heal info is showing all the files and dirs to be healed.
        14. Bring back all brick processes which were killed.
        15. Wait for heal to complete on the volume.
        16. Check if heal is complete and check if volume is in split brain.
        17. Collect and compare arequal-checksum according to the volume type
            for bricks.
        18. Bring down brick processes accoding to the volume type.
        19. Rename the existing files and dirs.
        20. Check if heal info is showing all the files and dirs to be healed.
        21. Bring back all brick processes which were killed.
        22. Wait for heal to complete on the volume.
        23. Check if heal is complete and check if volume is in split brain.
        24. Collect and compare arequal-checksum according to the volume type
            for bricks.

        Note:
        Do this test with both Granular-entry-heal set enable and disable.
        """
        for value in (False, True):
            if value:
                # Cleanup old data from mount point
                (self.redant.execute_abstract_op_node(
                 f"rm -rf {self.mountpoint}/*", self.client_list[0]))
            self._set_granular_heal_to_on_or_off(enabled=value)
            self._run_test_self_heal_entry_heal()

    def _test_self_heal_meta_data(self):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create a directory and create files and directories inside it
           on mount point.
        3. Collect and compare arequal-checksum according to the volume type
           for bricks.
        4. Bring down brick processes accoding to the volume type.
        5. Change the meta data of files and dirs.
        6. Check if heal info is showing all the files and dirs to be healed.
        7. Bring back all brick processes which were killed.
        8. Wait for heal to complete on the volume.
        9. Check if heal is complete and check if volume is in split brain.
        10. Collect and compare arequal-checksum according to the volume type
            for bricks.
        11. Verify if the meta data of files and dirs.
        12. Bring down brick processes accoding to the volume type.
        13. Set extended attributes on the files and dirs.
        14. Verify if the extended attributes are set properly or not.
        15. Check if heal info is showing all the files and dirs to be healed.
        16. Bring back all brick processes which were killed.
        17. Wait for heal to complete on the volume.
        18. Check if heal is complete and check if volume is in split brain.
        19. Collect and compare arequal-checksum according to the volume type
            for bricks.
        20. Verify if extended attributes are consitent or not.
        21. Bring down brick processes accoding to the volume type
        22. Remove extended attributes on the files and dirs.
        23. Verify if extended attributes were removed properly.
        24. Check if heal info is showing all the files and dirs to be healed.
        25. Bring back all brick processes which were killed.
        26. Wait for heal to complete on the volume.
        27. Check if heal is complete and check if volume is in split brain.
        28. Collect and compare arequal-checksum according to the volume type
            for bricks.
        29. Verify if extended attributes are removed or not.
        """
        self._setup_user()
        # Create a directory and create files and directories inside it
        # on mount point
        self._create_files_and_dirs_on_mount_point(1)

        # Collect and compare arequal-checksum according to the volume type
        # for bricks
        self._check_arequal_checksum_for_the_volume()

        # Bring down brick processes accoding to the volume type
        self._bring_bricks_offline()

        # Change the meta data of files and dirs
        self._change_meta_deta_of_dirs_and_files()

        self._check_heal_status_restart_vol_wait_and_check_data()

        # Verify if the meta data of files and dirs
        self._verify_meta_data_of_files_and_dirs()

        for value in (False, True):
            # Bring down brick processes accoding to the volume type
            self._bring_bricks_offline()

            # Set or remove extended attributes on the files and dirs
            self._set_and_remove_extended_attributes(remove=value)

            # Verify if the extended attributes are set properly or not
            self._verify_if_extended_attributes_are_proper(remove=value)

            self._check_heal_status_restart_vol_wait_and_check_data()

            # Verify if extended attributes are consitent or not
            self._verify_if_extended_attributes_are_proper(remove=value)

    def _test_self_heal_of_dir_with_files_removed(self):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create a directory and create files and directories inside it
           on mount point.
        3. Collect and compare arequal-checksum according to the volume type
           for bricks.
        4. Bring down brick processes accoding to the volume type.
        5. Remove all files and create dir which have name of files.
        6. Check if heal info is showing all the files and dirs to be healed.
        7. Bring back all brick processes which were killed.
        8. Wait for heal to complete on the volume.
        9. Check if heal is complete and check if volume is in split brain.
        10. Collect and compare arequal-checksum according to the volume type
            for bricks.
        11. Verify if dirs are healed properly or not.
        """
        # Create a directory and create files and directories inside it
        # on mount point
        self._create_files_and_dirs_on_mount_point(2)

        # Collect and compare arequal-checksum according to the volume type
        # for bricks
        self._check_arequal_checksum_for_the_volume()

        # Bring down brick processes accoding to the volume type
        self._bring_bricks_offline()

        # Remove all files and create dir which have name of files
        self._remove_files_and_create_dirs_with_the_same_name()

        self._check_heal_status_restart_vol_wait_and_check_data()

        # Verify if dirs are healed properly or not
        self._verify_if_dirs_are_proper_or_not()

    def run_test(self, redant):
        """
        1.TEST_SELF_HEAL_ENTRY_HEAL
        2.TEST_SELF_HEAL_META_DATA
        3.TEST_SELF_HEAL_OF_DIR_WITH_FILES_REMOVED
        """

        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        self.user_group_created = False

        self._test_self_heal_entry_heal()
        redant.logger.info("Test Case for entry heal is successful")
        self._test_self_heal_meta_data()
        redant.logger.info("Test Case for metadata heal is successful")
        self._test_self_heal_of_dir_with_files_removed()
        redant.logger.info("Test Case for dir with files removed "
                           "heal is successful")
