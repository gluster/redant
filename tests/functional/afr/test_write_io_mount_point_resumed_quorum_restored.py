"""
 Copyright (C) 2016-2020  Red Hat, Inc. <http://www.redhat.com>

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
    Test Cases in this module tests the client side quorum.
"""

# disruptive;dist-rep
from tests.d_parent_test import DParentTest


class TestClientSideQuorumRestored(DParentTest):

    def run_test(self, redant):
        """
        - set cluster.quorum-type to auto
        - start I/O from the mount point
        - Do IO and check on subvols with two nodes to reboot
        (do for each subvol)
        - get files to delete/create for nodes to be offline
        - delete files from mountpoint
        - reboot nodes
        - creating files on nodes while rebooting
        - validate for rofs
        - wait for volume processes to be online
        - creating files on nodes after rebooting
        - validate IO
        - Do IO and check on subvols without nodes to reboot
        (do for each subvol)
        - get files to delete/create for nodes to be online
        - delete files from mountpoint
        - reboot nodes
        - creating files on online nodes while rebooting other nodes
        - validate IO
        - Do IO and check and reboot two nodes on all subvols
        - get files to delete/create for nodes to be offline
        - delete files from mountpoint
        - reboot nodes
        - creating files on nodes while rebooting
        - validate for rofs
        - wait for volume processes to be online
        - creating files on nodes after rebooting
        - validate IO
        """
        script_file_path = "/usr/share/redant/script/file_dir_ops.py"

        # set cluster.quorum-type to auto
        options = {"cluster.quorum-type": "auto"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Creating files on client side
        for mount_obj in self.mounts:
            # Creating files
            cmd = (f"python3 {script_file_path} create_files -f 30 "
                   f"{mount_obj['mountpath']}")

            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")

        # Do IO and check on subvols with nodes to reboot
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        for subvol in subvols:
            # Define nodes to reboot
            nodes_to_reboot = []
            brick_list = subvol[0:2]
            for brick in brick_list:
                node, _ = brick.split(':')
                nodes_to_reboot.append(node)

            # get files to delete/create for nodes to be offline
            node, brick_path = brick_list[0].split(':')
            ret = redant.execute_abstract_op_node(f"ls {brick_path}", node)
            brick_file_list = "".join(ret['msg'])
            file_list = brick_file_list.split('\n')

            # delete files from mountpoint
            for mount_obj in self.mounts:
                cmd = (f"cd {mount_obj['mountpath']}/ ; rm -rf "
                       f"{' '.join(file_list)}")
                redant.execute_abstract_op_node(cmd, mount_obj['client'])

            # reboot nodes on subvol and wait while rebooting
            redant.reboot_nodes(nodes_to_reboot)

            # Creating files on nodes while rebooting
            for mount_obj in self.mounts:
                all_mounts_proc = []
                # Creating files
                cmd = (f"cd {mount_obj['mountpath']}/ ;"
                       f"touch {' '.join(file_list)}")
                proc = redant.execute_command_async(cmd, mount_obj['client'])
                all_mounts_proc.append(proc)

                # Validate IO
                ret, _ = redant.is_io_procs_fail_with_error(all_mounts_proc,
                                                            self.mounts)
                if not ret:
                    raise Exception("Unexpected error and IO successful"
                                    " on read-only filesystem")

            # check if nodes are online
            if not redant.wait_node_power_up(nodes_to_reboot, 300):
                raise Exception("Nodes not yet rebooted")

            # Wait for volume processes to be online
            if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                    self.server_list[0], self.server_list)):
                raise Exception("Few volume processess are offline for the "
                                f"volume: {self.vol_name}")

            # Verify volume's all process are online
            if not (redant.verify_all_process_of_volume_are_online(
                    self.vol_name, self.server_list[0])):
                raise Exception("Few process after volume start are offline "
                                f"for volume: {self.vol_name}")

            # Creating files on nodes after rebooting
            self.all_mounts_procs = []
            for mount_obj in self.mounts:
                # Creating files
                cmd = (f"cd {mount_obj['mountpath']}/ ;"
                       f"touch {' '.join(file_list)}")
                proc = redant.execute_command_async(cmd, mount_obj['client'])
                self.all_mounts_procs.append(proc)

            # Validate IO
            ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")

        # Do IO and check on subvols without nodes to reboot
        for subvol in subvols:
            # define nodes to reboot
            brick_list = subvol[0:2]
            nodes_to_reboot = []
            for brick in brick_list:
                node, _ = brick.split(':')
                nodes_to_reboot.append(node)

            # get files to delete/create for nodes to be online
            new_subvols = redant.get_subvols(self.vol_name,
                                             self.server_list[0])
            new_subvols.remove(subvol)
            brick_list_subvol_online = new_subvols[0]

            node, brick_path_vol_online = \
                brick_list_subvol_online[0].split(':')
            cmd = f"ls {brick_path_vol_online}"
            ret = redant.execute_abstract_op_node(cmd, node)
            brick_file_list = "".join(ret['msg'])
            file_list = brick_file_list.split('\n')

            # delete files from mountpoint
            for mount_obj in self.mounts:
                cmd = (f"cd {mount_obj['mountpath']}/ ; "
                       f"rm -rf {' '.join(file_list)}")
                redant.execute_abstract_op_node(cmd, mount_obj['client'])

            # reboot nodes on subvol and wait while rebooting
            redant.reboot_nodes(nodes_to_reboot)

            # Creating files on nodes while rebooting
            for mount_obj in self.mounts:
                self.all_mounts_procs = []
                # Creating files
                cmd = (f"cd {mount_obj['mountpath']}/ ;"
                       f"touch {' '.join(file_list)}")
                proc = redant.execute_command_async(cmd, mount_obj['client'])
                self.all_mounts_procs.append(proc)

                # Validate IO
                ret = redant.validate_io_procs(self.all_mounts_procs,
                                               self.mounts)
                if not ret:
                    raise Exception("IO failed on some of the clients")

            # check if nodes are online
            if not redant.wait_node_power_up(nodes_to_reboot, 300):
                raise Exception("Nodes not yet rebooted")

            # Wait for volume processes to be online
            if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                    self.server_list[0], self.server_list)):
                raise Exception("Few volume processess are offline for the "
                                f"volume: {self.vol_name}")

            # Verify volume's all process are online
            if not (redant.verify_all_process_of_volume_are_online(
                    self.vol_name, self.server_list[0])):
                raise Exception("Few process after volume start are offline "
                                f"for volume: {self.vol_name}")

        # Do IO and check and reboot nodes on all subvols
        nodes_to_reboot = []
        file_list_for_all_subvols = []
        for subvol in subvols:
            # define nodes to reboot
            brick_list = subvol[0:2]
            for brick in brick_list:
                node, _ = brick.split(':')
                nodes_to_reboot.append(node)

            # get files to delete/create for nodes to be offline
            node, brick_path = brick_list[0].split(':')
            ret = redant.execute_abstract_op_node(f"ls {brick_path}", node)
            brick_file_list = "".join(ret['msg'])
            file_list = brick_file_list.split('\n')
            file_list_for_all_subvols.append(file_list)

            # delete files from mountpoint
            for mount_obj in self.mounts:
                cmd = (f"cd {mount_obj['mountpath']}/ ; "
                       f"rm -rf {' '.join(file_list)}")
                redant.execute_abstract_op_node(cmd, mount_obj['client'])

        # reboot nodes on subvol and wait while rebooting
        redant.reboot_nodes(nodes_to_reboot)

        # Creating files on nodes while rebooting
        all_mounts_procs, all_mounts_procs_1, all_mounts_procs_2 = [], [], []
        # Create files for 1-st subvol and get all_mounts_procs_1
        for mount_obj in self.mounts:
            # Creating files
            cmd = (f"cd {mount_obj['mountpath']}/ ;"
                   f"touch {' '.join(file_list_for_all_subvols[0])}")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            all_mounts_procs_1.append(proc)
            all_mounts_procs.append(all_mounts_procs_1)

        # Create files for 2-st subvol and get all_mounts_procs_2
        for mount_obj in self.mounts:
            # Creating files
            cmd = (f"cd {mount_obj['mountpath']}/ ;"
                   f"touch {' '.join(file_list_for_all_subvols[1])}")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            all_mounts_procs_2.append(proc)
            all_mounts_procs.append(all_mounts_procs_2)

        for mounts_procs in all_mounts_procs:
            # Validate IO
            ret, _ = redant.is_io_procs_fail_with_error(mounts_procs,
                                                        self.mounts)
            if not ret:
                raise Exception("Unexpected error and IO successful"
                                " on read-only filesystem")

        # check if nodes are online
        if not redant.wait_node_power_up(nodes_to_reboot, 300):
            raise Exception("Nodes not yet rebooted")

        # Wait for volume processes to be online
            if not (redant.wait_for_volume_process_to_be_online(self.vol_name,
                    self.server_list[0], self.server_list)):
                raise Exception("Few volume processess are offline for the "
                                f"volume: {self.vol_name}")

            # Verify volume's all process are online
            if not (redant.verify_all_process_of_volume_are_online(
                    self.vol_name, self.server_list[0])):
                raise Exception("Few process after volume start are offline "
                                f"for volume: {self.vol_name}")

        # Creating files on nodes after rebooting
        all_mounts_procs, all_mounts_procs_1, all_mounts_procs_2 = [], [], []
        # Create files for 1-st subvol and get all_mounts_procs_1
        for mount_obj in self.mounts:
            # Creating files
            cmd = (f"cd {mount_obj['mountpath']}/ ;"
                   f"touch {' '.join(file_list_for_all_subvols[0])}")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            all_mounts_procs_1.append(proc)
            all_mounts_procs.append(all_mounts_procs_1)

        # Create files for 2-st subvol and get all_mounts_procs_2
        for mount_obj in self.mounts:
            # Creating files
            cmd = (f"cd {mount_obj['mountpath']}/ ;"
                   f"touch {' '.join(file_list_for_all_subvols[1])}")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            all_mounts_procs_2.append(proc)
            all_mounts_procs.append(all_mounts_procs_2)

        for mounts_procs in all_mounts_procs:
            # Validate IO
            ret = redant.validate_io_procs(mounts_procs, self.mounts)
            if not ret:
                raise Exception("IO failed on some of the clients")
