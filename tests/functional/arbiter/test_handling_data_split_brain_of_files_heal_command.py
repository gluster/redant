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
    Arbiter Test cases related to
    healing in default configuration of the volume
"""

# disruptive;arb
# TODO: nfs, cifs

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def run_test(self, redant):
        """
        - create IO
        - calculate arequal from mountpoint
        - set volume option 'self-heal-daemon' to value "off"
        - kill data brick1
        - calculate arequal checksum and compare it
        - modify files and directories
        - bring back all bricks processes online
        - kill data brick3
        - modify files and directories
        - calculate arequal from mountpoint
        - bring back all bricks processes online
        - run the find command to trigger heal from mountpoint
        - set volume option 'self-heal-daemon' to value "on"
        - check if heal is completed
        - check for split-brain
        - read files
        - calculate arequal checksum and compare it
        """
        self.all_mounts_procs = []
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Creating files on client side
        for mount_obj in self.mounts:
            # Create files
            command = (f"cd {mount_obj['mountpath']} ; "
                       "for i in `seq 1 10` ; "
                       "do mkdir dir.$i ; "
                       "for j in `seq 1 5` ; "
                       "do dd if=/dev/urandom of=dir.$i/file.$j "
                       "bs=1K count=1 ; "
                       "done ; "
                       "dd if=/dev/urandom of=file.$i bs=1k count=1 ; "
                       "done")

            proc = redant.execute_command_async(command,
                                                mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # Get arequal before getting bricks offline
        result_before_offline = (redant.
                                 collect_mounts_arequal(self.mounts))

        # Setting options
        options = {"self-heal-daemon": "off"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # get the bricks for the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])

        # Bring brick 1 offline
        bricks_to_bring_offline = [bricks_list[0]]
        redant.bring_bricks_offline(self.vol_name,
                                    bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f'Bricks {bricks_to_bring_offline}'
                            ' are not offline')

        # Get arequal after getting bricks offline
        result_after_offline = (redant.
                                collect_mounts_arequal(self.mounts))

        # Comparing arequals before getting bricks offline
        # and after getting bricks offline
        if result_after_offline != result_before_offline:
            raise Exception('Arequals before getting bricks offline '
                            'and after getting bricks offline are'
                            ' not equal')

        # Modify the data
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # Modify files
            command = (f"cd {mount_obj['mountpath']} ; "
                       "for i in `seq 1 10` ; "
                       "do for j in `seq 1 5` ; "
                       "do dd if=/dev/urandom of=dir.$i/file.$j "
                       "bs=1M count=1 ; "
                       "done ; "
                       "dd if=/dev/urandom of=file.$i bs=1M count=1 ; "
                       "done")

            proc = redant.execute_command_async(command,
                                                mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # Bring 1-st brick online
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_to_bring_offline)
        if not redant.are_bricks_online(self.vol_name,
                                        bricks_to_bring_offline,
                                        self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline}"
                            " are not online.")

        # Bring brick 3rd offline
        bricks_to_bring_offline = [bricks_list[-1]]
        redant.bring_bricks_offline(self.vol_name,
                                    bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f'Bricks {bricks_to_bring_offline}'
                            ' are not offline')

        # Modify the data
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # Create files
            command = (f"cd {mount_obj['mountpath']} ; "
                       "for i in `seq 1 10` ; "
                       "do for j in `seq 1 5` ; "
                       "do dd if=/dev/urandom of=dir.$i/file.$j "
                       "bs=1M count=1 ; "
                       "done ; "
                       "dd if=/dev/urandom of=file.$i bs=1M count=1 ; "
                       "done")

            proc = redant.execute_command_async(command,
                                                mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # Get arequal before getting bricks online
        result_before_online = redant.collect_mounts_arequal(self.mounts)

        # Bring 3rd brick online
        redant.bring_bricks_online(self.vol_name, self.server_list,
                                   bricks_to_bring_offline)
        if not redant.are_bricks_online(self.vol_name,
                                        bricks_to_bring_offline,
                                        self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline}"
                            " are not online.")

        # Mount and unmount mounts
        for client in self.client_list:
            redant.volume_unmount(self.vol_name, self.mountpoint,
                                  client)

            redant.volume_mount(self.server_list[0], self.vol_name,
                                self.mountpoint, client)

        # Start heal from mount point
        for mount_obj in self.mounts:
            command = ("python3 /tmp/file_dir_ops.py "
                       f"read {mount_obj['mountpath']}")
            redant.execute_abstract_op_node(command,
                                            mount_obj['client'])
        options = {"self-heal-daemon": "on"}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0])

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet finished")

        # is heal complete testing
        if not redant.is_heal_complete(self.server_list[0],
                                       self.vol_name):
            raise Exception("Heal not yet finished")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume in split-brain")

        # Reading files
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            command = (f'cd {mount_obj["mountpath"]} ; '
                       'for i in `seq 1 10` ; '
                       'do cat file.$i > /dev/null ; '
                       'for j in `seq 1 5` ; '
                       'do cat dir.$i/file.$j > /dev/null ; '
                       'done ; done')
            proc = redant.execute_command_async(command,
                                                mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs,
                                        self.mounts):
            raise Exception("IO failed on some of the clients")

        # Get arequal after getting bricks online
        result_after_online = redant.collect_mounts_arequal(self.mounts)

        # Comparing arequals before getting bricks online
        # and after getting bricks online
        if result_after_online != result_before_online:
            raise Exception('Arequals before getting bricks online '
                            'and after getting bricks online are'
                            ' not equal')
