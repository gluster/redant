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
    TC to check metadata self-heal on client side heal
"""

# disruptive;rep,dist-rep
import traceback
from tests.d_parent_test import DParentTest


class TestAFRMetaDataSelfHealClientSideHeal(DParentTest):

    def terminate(self):
        """
        Delete the users created in the test"
        """
        try:
            for mount_obj in self.mounts:
                for user in self.users:
                    if not self.redant.del_user(mount_obj['client'], user):
                        raise Exception(f"Failed to delete user {user}")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def trigger_heal_from_mount_point(self):
        """
        Trigger heal from mount point using read.
        """
        # Unmouting and remounting volume to update the volume graph
        # in client.
        self.redant.volume_unmount(self.vol_name, self.mountpoint,
                                   self.client_list[0])

        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

        # Trigger heal from client side
        cmd = (f"python3 /usr/share/redant/script/file_dir_ops.py read"
               f"{self.mountpoint}/{self.self_heal_folder}")
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def validate_io_on_clients(self):
        """
        Validate I/O on client mount points.
        """
        ret = self.redant.validate_io_procs(self.all_mounts_procs,
                                            self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

    def check_arequal_from_mount_point_and_bricks(self):
        """
        Check if arequals of mount point and bricks are
        are the same.
        """
        # Check arequals for "replicated"
        all_bricks = self.redant.get_all_bricks(self.vol_name,
                                                self.server_list[0])
        if not all_bricks:
            raise Exception("Failed to get brick list")

        if self.volume_type == "rep":
            # Get mount arequal before getting bricks offline
            arequals = self.redant.collect_mounts_arequal(self.mounts)
            mount_point_total = arequals[0][-1].split(':')[-1]

            # Get arequal on bricks and compare with mount_point_total
            arequals = self.redant.collect_bricks_arequal(all_bricks)
            for arequal in arequals:
                brick_total = arequal[-1].split(':')[-1]
                if mount_point_total != brick_total:
                    raise Exception('Arequals for mountpoint and brick '
                                    'are not equal')
        else:
            # Check arequals for "distributed-replicated"
            # get the subvolumes
            subvols = self.redant.get_subvols(self.vol_name,
                                              self.server_list[0])
            if not subvols:
                raise Exception("Failed to get the subvols for the volume")
            num_subvols = len(subvols)

            # Get arequals and compare
            for i in range(0, num_subvols):
                # Get arequal for first brick
                arequal = self.redant.collect_bricks_arequal(subvols[i][0])
                first_brick_total = arequal[0][-1].split(':')[-1]

                # Get arequal for every brick and compare with first brick
                arequals = self.redant.collect_bricks_arequal(subvols[i])
                for arequal in arequals:
                    brick_total = arequal[-1].split(':')[-1]
                    if first_brick_total != brick_total:
                        raise Exception('Arequals for subvol and brick are '
                                        'not equal')

    def check_permssions_on_bricks(self, bricks_list):
        """
        Check permssions on a given set of bricks.
        """
        for brick in bricks_list:
            node, brick_path = brick.split(':')
            path = f"{brick_path}/{self.self_heal_folder}"
            dir_list = self.redant.get_dir_contents(path, node)
            if dir_list is None:
                raise Exception("Dir list from brick is empty")

            # Verify changes for dirs
            for folder in dir_list:
                folder_path = f"{path}/{folder}"
                ret = self.redant.get_file_stat(node, folder_path)
                if ret['error_code'] != 0:
                    raise Exception("Failed to stat path")

                if ret['msg']['permission'] != 555:
                    raise Exception(f"Permissions mismatch on node {node}")

                if ret['msg']['st_gid'] != (1003 + self.is_user_present):
                    raise Exception(f"Group id mismatch on node {node}")

                # Get list of files for each dir
                file_list = self.redant.get_dir_contents(folder_path, node)
                if file_list is None:
                    raise Exception("File list from brick is empty")

                # Verify for group for each file
                for file_name in file_list:
                    file_path = f"{folder_path}/{file_name}"
                    ret = self.redant.get_file_stat(node, file_path)
                    if ret['error_code'] != 0:
                        raise Exception("Failed to stat path")

                    if ret['msg']['st_gid'] != (1003 + self.is_user_present):
                        raise Exception(f"Group id mismatch on node {node}"
                                        f" for file {file_name}")

            # Verify permissions for files in dirs 1..50
            for i in range(1, 51):
                path = f"{brick_path}/{self.self_heal_folder}/dir.{i}"
                file_list = self.redant.get_dir_contents(path, node)
                if file_list is None:
                    raise Exception("File list from brick is empty")

                for file_name in file_list:
                    file_path = f"{path}/{file_name}"
                    ret = self.redant.get_file_stat(node, file_path)
                    if ret['error_code'] != 0:
                        raise Exception("Failed to stat path")

                    if ret['msg']['permission'] != 666:
                        raise Exception(f"Permissions mismatch on node {node}")

            # Verify permissions for files in dirs 51..100
            for i in range(51, 101):
                path = f"{brick_path}/{self.self_heal_folder}/dir.{i}"
                file_list = self.redant.get_dir_contents(path, node)
                if file_list is None:
                    raise Exception("File list from brick is empty")

                for file_name in file_list:
                    file_path = f"{path}/{file_name}"
                    ret = self.redant.get_file_stat(node, file_path)
                    if ret['error_code'] != 0:
                        raise Exception("Failed to stat path")

                    if ret['msg']['permission'] != 444:
                        raise Exception(f"Permissions mismatch on node {node}")

            # Verify ownership for dirs 1..35
            for i in range(1, 36):
                dir_path = f"{brick_path}/{self.self_heal_folder}/dir.{i}"
                ret = self.redant.get_file_stat(node, dir_path)
                if ret['error_code'] != 0:
                    raise Exception("Failed to stat path")
                if ret['msg']['st_uid'] != (1000 + self.is_user_present):
                    raise Exception(f"User id mismatch on node {node}")

                # Verify ownership for files in dirs
                file_list = self.redant.get_dir_contents(dir_path, node)
                if file_list is None:
                    raise Exception("File list from brick is empty")

                for file_name in file_list:
                    file_path = f"{dir_path}/{file_name}"
                    ret = self.redant.get_file_stat(node, file_path)
                    if ret['error_code'] != 0:
                        raise Exception("Failed to stat path")

                    if ret['msg']['st_uid'] != (1000 + self.is_user_present):
                        raise Exception(f"Permissions mismatch on node {node}")

            # Verify ownership for dirs 36..70
            for i in range(36, 71):
                dir_path = f"{brick_path}/{self.self_heal_folder}/dir.{i}"
                ret = self.redant.get_file_stat(node, dir_path)
                if ret['error_code'] != 0:
                    raise Exception("Failed to stat path")
                if ret['msg']['st_uid'] != (1001 + self.is_user_present):
                    raise Exception(f"User id mismatch on node {node}")

                # Verify ownership for files in dirs
                file_list = self.redant.get_dir_contents(dir_path, node)
                if file_list is None:
                    raise Exception("File list from brick is empty")

                for file_name in file_list:
                    file_path = f"{dir_path}/{file_name}"
                    ret = self.redant.get_file_stat(node, file_path)
                    if ret['error_code'] != 0:
                        raise Exception("Failed to stat path")

                    if ret['msg']['st_uid'] != (1001 + self.is_user_present):
                        raise Exception(f"Permissions mismatch on node {node}")

            # Verify ownership for dirs 71..100
            for i in range(71, 101):
                dir_path = f"{brick_path}/{self.self_heal_folder}/dir.{i}"
                ret = self.redant.get_file_stat(node, dir_path)
                if ret['error_code'] != 0:
                    raise Exception("Failed to stat path")
                if ret['msg']['st_uid'] != (1002 + self.is_user_present):
                    raise Exception(f"User id mismatch on node {node}")

                # Verify ownership for files in dirs
                file_list = self.redant.get_dir_contents(dir_path, node)
                if file_list is None:
                    raise Exception("File list from brick is empty")

                for file_name in file_list:
                    file_path = f"{dir_path}/{file_name}"
                    ret = self.redant.get_file_stat(node, file_path)
                    if ret['error_code'] != 0:
                        raise Exception("Failed to stat path")

                    if ret['msg']['st_uid'] != (1002 + self.is_user_present):
                        raise Exception(f"Permissions mismatch on node {node}")

    def run_test(self, redant):
        """
        Testcase steps:
        1.Turn off the options self heal daemon
        2.Create IO
        3.Calculate arequal of the bricks and mount point
        4.Bring down "brick1" process
        5.Change the permissions of the directories and files
        6.Change the ownership of the directories and files
        7.Change the group of the directories and files
        8.Bring back the brick "brick1" process
        9.Execute "find . | xargs stat" from the mount point to trigger heal
        10.Verify the changes in permissions are not self healed on brick1
        11.Verify the changes in permissions on all bricks but brick1
        12.Verify the changes in ownership are not self healed on brick1
        13.Verify the changes in ownership on all the bricks but brick1
        14.Verify the changes in group are not successfully self-healed
           on brick1
        15.Verify the changes in group on all the bricks but brick1
        16.Turn on the option metadata-self-heal
        17.Execute "find . | xargs md5sum" from the mount point to trgger heal
        18.Wait for heal to complete
        19.Verify the changes in permissions are self-healed on brick1
        20.Verify the changes in ownership are successfully self-healed
           on brick1
        21.Verify the changes in group are successfully self-healed on brick1
        22.Calculate arequal check on all the bricks and mount point
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Checking if we have a non-root user already
        self.is_user_present = 0
        cmd = "id -un 1000"
        ret = redant.execute_abstract_op_node(cmd, self.client_list[0], False)
        if ret['error_code'] == 0:
            self.is_user_present = 1

        # Create new users on clients
        self.users = ['qa_func', 'qa_system', 'qa_perf', 'qa_all']
        for mount_obj in self.mounts:
            for user in self.users:
                if not redant.add_user(mount_obj['client'], user):
                    raise Exception(f"Failed to create user {user}")

        # Setting options
        options = {"self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Creating files on client side
        self.self_heal_folder = 'test_meta_data_self_heal'
        for mount_obj in self.mounts:
            cmd = (f"cd {mount_obj['mountpath']}/ ; "
                   f"mkdir {self.self_heal_folder} ; "
                   f"cd {self.self_heal_folder}/ ; for i in `seq 1 100` ; "
                   "do mkdir dir.$i ; for j in `seq 1 5` ; do dd "
                   "if=/dev/urandom of=dir.$i/file.$j bs=1K count=$j ; "
                   "done ; done ;")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        self.validate_io_on_clients()

        # Calculate and check arequal of the bricks and mount point
        self.check_arequal_from_mount_point_and_bricks()

        # Select bricks to bring offline from a replica set
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols for the volume")
        bricks_to_bring_offline = []
        bricks_to_be_online = []
        for subvol in subvols:
            bricks_to_bring_offline.append(subvol[0])
            for brick in subvol[1:]:
                bricks_to_be_online.append(brick)

        # Bring bricks offline
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} are not "
                            "offline")

        # Change the permissions of the directories and files
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            cmd = (f"cd {mount_obj['mountpath']}/{self.self_heal_folder}; "
                   "for i in `seq 1 100` ; do chmod 555 dir.$i ; done ; "
                   "for i in `seq 1 50` ; do for j in `seq 1 5` ; "
                   "do chmod 666 dir.$i/file.$j ; done ; done ; "
                   "for i in `seq 51 100` ; do for j in `seq 1 5` ; "
                   "do chmod 444 dir.$i/file.$j ; done ; done ;")

            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        self.validate_io_on_clients()

        # Change the ownership of the directories and files
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            cmd = (f"cd {mount_obj['mountpath']}/{self.self_heal_folder} ; "
                   "for i in `seq 1 35` ; do chown -R qa_func dir.$i ; done ;"
                   " for i in `seq 36 70` ; do chown -R qa_system dir.$i ; "
                   "done ; for i in `seq 71 100` ; do chown -R qa_perf dir.$i"
                   " ; done ;")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        self.validate_io_on_clients()

        # Change the group of the directories and files
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            cmd = (f"cd {mount_obj['mountpath']}/{self.self_heal_folder}; "
                   "for i in `seq 1 100` ; do chgrp -R qa_all dir.$i; done;")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        self.validate_io_on_clients()

        # Bring brick online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          bricks_to_bring_offline):
            raise Exception("Failed to bring bricks "
                            f"{bricks_to_bring_offline} online")

        # Trigger heal from mount point
        self.trigger_heal_from_mount_point()

        # Verify if the changes are self healed or not for offline bricks
        for brick in bricks_to_bring_offline:
            node, brick_path = brick.split(':')

            path = f"{brick_path}/{self.self_heal_folder}"
            dir_list = redant.get_dir_contents(path, node)
            if dir_list is None:
                raise Exception("Dir list from brick is empty")

            # Verify changes for dirs
            for folder in dir_list:
                folder_path = f"{path}/{folder}"
                ret = redant.get_file_stat(node, folder_path)
                if ret['error_code'] != 0:
                    raise Exception("Failed to stat path")

                if ret['msg']['permission'] != 755:
                    raise Exception(f"Permissions mismatch on node {node}")

                if ret['msg']['user'] != 'root':
                    raise Exception(f"User mismatch on node {node}")

                if ret['msg']['group'] != 'root':
                    raise Exception(f"Group mismatch on node {node}")

                # Get list of files for each dir
                file_list = redant.get_dir_contents(folder_path, node)
                if file_list is None:
                    raise Exception("File list from brick is empty")

                for file_name in file_list:
                    file_path = f"{folder_path}/{file_name}"
                    ret = redant.get_file_stat(node, file_path)
                    if ret['error_code'] != 0:
                        raise Exception("Failed to stat path")

                    if ret['msg']['permission'] != 644:
                        raise Exception(f"Permissions mismatch on node {node}"
                                        f" for file {file_name}")

                    if ret['msg']['user'] != 'root':
                        raise Exception(f"User mismatch on node {node}"
                                        f" for file {file_name}")

                    if ret['msg']['group'] != 'root':
                        raise Exception(f"Group mismatch on node {node}"
                                        f" for file {file_name}")

        # Verify the changes are self healed on all bricks except brick1
        # for each subvol
        self.check_permssions_on_bricks(bricks_to_be_online)

        # Setting options
        options = {"metadata-self-heal": "on"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Trigger heal from mount point
        self.trigger_heal_from_mount_point()

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

        # Verify the changes are self healed on brick1 for each subvol
        self.check_permssions_on_bricks(bricks_to_bring_offline)

        # Calculate and check arequal of the bricks and mount point
        self.check_arequal_from_mount_point_and_bricks()
