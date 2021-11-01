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
    TC to verify shd heals files after performing various file/dir
    operations while a brick was down.
"""

# disruptive;arb,rep
import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    def terminate(self):
        # Delete group and user names created as part of setup
        try:
            # Delete user on client
            self.redant.del_user(self.client_list[0], 'qa_all')

            # Delete group on client
            for group in ('qa_func', 'qa_system'):
                self.redant.group_del(self.client_list[0], group)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _dac_helper(self, host, option, testtype=None):
        """
        Helper for creating, deleting users and groups
        """
        # Permission/Ownership changes required only for `test_metadata..`
        # tests, using random group and usernames
        if testtype != "metadata":
            return

        if option == 'create':
            # Groups
            for group in ("qa_func", "qa_system"):
                if not self.redant.group_add(host, group):
                    raise Exception(f"Unable to {option} group {group} on "
                                    f"{host}")

            # User
            if not self.redant.add_user(host, "qa_all", group="qa_func"):
                raise Exception(f"Unable to {option} user 'qa_all' under"
                                f" 'qa_func' on {host}")

        elif option == 'delete':
            # Groups
            for group in ('qa_func', 'qa_system'):
                if not self.redant.group_del(host, group):
                    raise Exception(f"Unable to {option} group {group} on "
                                    f"{host}")

            # User
            if not self.redant.del_user(host, 'qa_all'):
                raise Exception(f"Unable to {option} user 'qa_all' on {host}")

    def _initial_io(self):
        """Initial IO operations: Different tests might need different IO"""
        # Create 6 dir's, 6 files and 6 files in each subdir with 10K data
        file_io = (f"cd {self.fqpath}; for i in `seq 1 6`; do mkdir dir.$i;"
                   f" {self.io_cmd} 10K > file.$i; for j in `seq 1 6`; do "
                   f"{self.io_cmd} 10K > dir.$i/file.$j; done; done;")
        self.redant.execute_abstract_op_node(file_io, self.client)

    def _perform_io_and_disable_self_heal(self, initial_io=None):
        """
        Refactor of steps common to all tests: Perform IO, disable heal
        """
        self.redant.create_dir(self.mountpoint, self.test_dir,
                               self.client_list[0])

        if initial_io is not None:
            initial_io()

        # Disable self heal deamon
        if not self.redant.disable_self_heal_daemon(self.vol_name,
                                                    self.server_list[0]):
            raise Exception("Disabling self-heal-daemon falied")

    def _perform_brick_ops_and_enable_self_heal(self, op_type):
        """
        Refactor of steps common to all tests: Brick down and perform
        metadata/data operations
        """
        # First brick in the subvol will always be online and used for self
        # heal, so make keys match brick index
        self.op_cmd = {
            # The operation with key `4` in every op_type will be used for
            # final data consistency check
            # Metadata Operations (owner and permission changes)
            'metadata': {
                2:
                '''cd {0}; for i in `seq 1 3`; do chown -R qa_all:qa_func \
                dir.$i file.$i; chmod -R 555 dir.$i file.$i; done;''',
                3:
                '''cd {0}; for i in `seq 1 3`; do chown -R :qa_system \
                dir.$i file.$i; chmod -R 777 dir.$i file.$i; done;''',
                4:
                '''cd {0}; for i in `seq 1 6`; do chown -R qa_all:qa_system \
                dir.$i file.$i; chmod -R 777 dir.$i file.$i; done;''',
            },
            # Data Operations (append data to the files)
            'data': {
                2:
                '''cd {0}; for i in `seq 1 3`;
                    do {1} 2K >> file.$i;
                    for j in `seq 1 3`;
                    do {1} 2K >> dir.$i/file.$j; done;
                    done;''',
                3:
                '''cd {0}; for i in `seq 1 3`;
                    do {1} 3K >> file.$i;
                    for j in `seq 1 3`;
                    do {1} 3K >> dir.$i/file.$j; done;
                    done;''',
                4:
                '''cd {0}; for i in `seq 1 6`;
                    do {1} 4K >> file.$i;
                    for j in `seq 1 6`;
                    do {1} 4K >> dir.$i/file.$j; done;
                    done;''',
            },
            # Create files and directories when brick is down with no
            # initial IO
            'gfid': {
                2:
                '''cd {0}; for i in `seq 1 3`;
                    do {1} 2K > file.2.$i; mkdir dir.2.$i;
                    for j in `seq 1 3`;
                    do {1} 2K > dir.2.$i/file.2.$j; done;
                    done;''',
                3:
                '''cd {0}; for i in `seq 1 3`;
                    do {1} 2K > file.3.$i; mkdir dir.3.$i;
                    for j in `seq 1 3`;
                    do {1} 2K > dir.3.$i/file.3.$j; done;
                    done;''',
                4:
                '''cd {0}; for i in `seq 4 6`;
                    do {1} 2K > file.$i; mkdir dir.$i;
                    for j in `seq 4 6`;
                    do {1} 2K > dir.$i/file.$j; done;
                    done;''',
            },
            # Create different file type with same name while a brick was down
            # with no initial IO and validate failure
            'file_type': {
                2:
                'cd {0}; for i in `seq 1 6`; do {1} 2K > notype.$i; done;',
                3:
                'cd {0}; for i in `seq 1 6`; do mkdir -p notype.$i; done;',
                4:
                '''cd {0}; for i in `seq 1 6`;
                    do {1} 2K > file.$i;
                    for j in `seq 1 6`;
                    do mkdir -p dir.$i; {1} 2K > dir.$i/file.$j; done;
                    done;''',
            },
            # Create symlinks for files and directories while a brick was down
            # Out of 6 files, 6 dirs and 6 files in each dir, symlink
            # outer 2 files, inner 2 files in each dir, 2 dirs and
            # verify it's a symlink(-L) and linking file exists(-e)
            'symlink': {
                2:
                '''cd {0}; for i in `seq 1 2`;
                    do ln -sr file.$i sl_file.2.$i;
                    [ -L sl_file.2.$i ] && [ -e sl_file.2.$i ] || exit -1;
                    for j in `seq 1 2`;
                    do ln -sr dir.$i/file.$j dir.$i/sl_file.2.$j; done;
                    [ -L dir.$i/sl_file.2.$j ] && [ -e dir.$i/sl_file.2.$j ] \
                    || exit -1;
                    done; for k in `seq 3 4`; do ln -sr dir.$k sl_dir.2.$k;
                    [ -L sl_dir.2.$k ] && [ -e sl_dir.2.$k ] || exit -1;
                    done;''',
                3:
                '''cd {0}; for i in `seq 1 2`;
                    do ln -sr file.$i sl_file.3.$i;
                    [ -L sl_file.3.$i ] && [ -e sl_file.3.$i ] || exit -1;
                    for j in `seq 1 2`;
                    do ln -sr dir.$i/file.$j dir.$i/sl_file.3.$j; done;
                    [ -L dir.$i/sl_file.3.$j ] && [ -e dir.$i/sl_file.3.$j ] \
                    || exit -1;
                    done; for k in `seq 3 4`; do ln -sr dir.$k sl_dir.3.$k;
                    [ -L sl_dir.3.$k ] && [ -e sl_dir.3.$k ] || exit -1;
                    done;''',
                4:
                '''cd {0}; ln -sr dir.4 sl_dir_new.4; mkdir sl_dir_new.4/dir.1;
                    {1} 4K >> sl_dir_new.4/dir.1/test_file;
                    {1} 4K >> sl_dir_new.4/test_file;
                    ''',
            },
        }
        bricks = self.redant.get_online_bricks_list(self.vol_name,
                                                    self.server_list[0])
        if bricks is None:
            raise Exception('Not able to get list of bricks in the volume')

        # Make first brick always online and start operations from second brick
        for index, brick in enumerate(bricks[1:], start=2):

            # Bring brick offline
            if not self.redant.bring_bricks_offline(self.vol_name, brick):
                raise Exception(f"Unable to bring {brick} offline")

            if not self.redant.are_bricks_offline(self.vol_name, brick,
                                                  self.server_list[0]):
                raise Exception(f"Brick {brick} is not offline")

            # Perform file/dir operation
            cmd = self.op_cmd[op_type][index].format(self.fqpath, self.io_cmd)
            ret = self.redant.execute_abstract_op_node(cmd, self.client,
                                                       False)
            if op_type == 'file_type' and index == 3:
                # Should fail with ENOTCONN as one brick is down, lookupt can't
                # happen and quorum is not met
                if ret['error_code'] == 0:
                    raise Exception("{0} should fail as lookup fails, quorum"
                                    " is not met".format(cmd))
                if "Transport" not in ret['error_msg']:
                    raise Exception("{0} should fail with ENOTCONN error"
                                    .format(cmd))
            else:
                if ret['error_code'] != 0:
                    raise Exception("{0} failed with {1}".format(cmd,
                                    ret['error_msg']))

            # Bring brick online
            if not self.redant.bring_bricks_online(self.vol_name,
                                                   self.server_list,
                                                   brick):
                raise Exception("Failed to bring bricks online")

            if not self.redant.are_bricks_online(self.vol_name, brick,
                                                 self.server_list[0]):
                raise Exception(f"Brick {brick} is not online")

            # Buffer to allow volume to be mounted
            sleep(4)

        # Confirm metadata/data operations resulted in pending heals
        if self.redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Heal is not yet complete")

        # Enable and wait self heal daemon to be online
        if not self.redant.enable_self_heal_daemon(self.vol_name,
                                                   self.server_list[0]):
            raise Exception("Enabling self heal daemon failed")

        if not (self.redant.wait_for_self_heal_daemons_to_be_online(
                self.vol_name, self.server_list[0])):
            raise Exception('Not all self heal daemons are online')

    def _validate_heal_completion_and_arequal(self, op_type):
        """Refactor of steps common to all tests: Validate heal from heal
           commands, verify arequal, perform IO and verify arequal after IO"""

        # Validate heal completion
        if not self.redant.monitor_heal_completion(self.server_list[0],
                                                   self.vol_name):
            raise Exception("Heal is not yet finished")

        if self.redant.is_volume_in_split_brain(self.server_list[0],
                                                self.vol_name):
            raise Exception("Volume in split-brain")

        subvols = self.redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Not able to get list of subvols")

        arbiter = self.volume_type.find('arb') >= 0
        stop = len(subvols[0]) - 1 if arbiter else len(subvols[0])

        # Validate arequal
        self._validate_arequal_and_perform_lookup(subvols, stop)

        # Perform some additional metadata/data operations
        cmd = self.op_cmd[op_type][4].format(self.fqpath, self.io_cmd)
        self.redant.execute_abstract_op_node(cmd, self.client)

        # Validate arequal after additional operations
        self._validate_arequal_and_perform_lookup(subvols, stop)

    def _validate_arequal_and_perform_lookup(self, subvols, stop):
        """Refactor of steps common to all tests: Validate arequal from
           bricks backend and perform a lookup of all files from mount"""
        arequal = None
        for subvol in subvols:
            new_arequal = []
            arequal = self.redant.collect_bricks_arequal(subvol[0:stop])
            for item in arequal:
                item = " ".join(item)
                new_arequal.append(item)

            if len(set(new_arequal)) != 1:
                raise Exception("Mismatch of `arequal` checksum among "
                                f"{subvol[0:stop]} is identified")

        # Validate arequal of mount point matching against backend bricks
        mp_arequal = self.redant.collect_mounts_arequal(self.mounts)
        mp_arequal = [" ".join(mp_arequal[0])]
        if len(set(new_arequal + mp_arequal)) != 1:
            raise Exception("Mismatch of `arequal` checksum among "
                            "bricks and mount is identified")

        # Perform a lookup of all files and directories on mounts
        if not self.redant.list_all_files_and_dirs_mounts(self.mounts):
            raise Exception("Failed to list all files and dirs from mount")

    def _test_driver(self, op_type, invoke_heal=False, initial_io=None):
        # Driver for all tests
        self._perform_io_and_disable_self_heal(initial_io=initial_io)
        self._perform_brick_ops_and_enable_self_heal(op_type=op_type)
        if invoke_heal:
            # Invoke `glfsheal
            if not self.redant.trigger_heal(self.vol_name,
                                            self.server_list[0]):
                raise Exception("Unable to trigger index heal on the volume")

        self._validate_heal_completion_and_arequal(op_type=op_type)

    def run_test(self, redant):
        """
        Generic Steps:
        1. Create, mount a volume and run IO except for gfid tests
        2. Disable self heal, perform cyclic brick down and make sure one data
           brick is always online
        3. While brick was down perform various operations (data, metadata,
           gfid, different file types, symlink) one for each test
        4. When all the bricks are up, enable self heal, wait for heal
           completion
        5. Validate arequal checksum, perform IO corresponding to earlier
           operations and validate arequal checksum for final data consistency.
        """
        # A single mount is enough for all the tests
        self.mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        self.client = self.client_list[0]

        # Use testcase name as test directory
        self.test_dir = self.test_name
        self.fqpath = f"{self.mountpoint}/{self.test_dir}"
        self.io_cmd = "cat /dev/urandom | tr -dc [:space:][:print:] | head -c"

        # Test for test_metadata_heal_from_shd
        # Crete group and user names required for the test
        self._dac_helper(host=self.client, option='create',
                         testtype='metadata')

        self._test_driver(op_type='metadata', initial_io=self._initial_io)
        redant.logger.info("Pass: Verification of metadata heal after "
                           "switching on `self heal daemon` is complete")

        self._dac_helper(host=self.client, option='delete',
                         testtype='metadata')

        # Test for test_metadata_heal_from_heal_cmd
        self._dac_helper(host=self.client, option='create',
                         testtype='metadata')

        self._test_driver(op_type='metadata', invoke_heal=True,
                          initial_io=self._initial_io)
        redant.logger.info("Pass: Verification of metadata heal via "
                           "`glfsheal` is complete")

        self._dac_helper(host=self.client, option='delete',
                         testtype='metadata')

        # Test for test_data_heal_from_shd
        self._test_driver(op_type='data', initial_io=self._initial_io)
        redant.logger.info("Pass: Verification of data heal after switching"
                           " on `self heal daemon` is complete")

        # Test for test_gfid_heal_from_shd
        self._test_driver(op_type='gfid')
        redant.logger.info("Pass: Verification of gfid heal after switching"
                           " on `self heal daemon` is complete")

        # Test for test_file_type_differs_heal_from_shd
        self._test_driver(op_type='file_type')
        redant.logger.info("Pass: Verification of gfid heal with "
                           "different file types after switching on "
                           "`self heal daemon` is complete")

        # Test for test_sym_link_heal_from_shd
        self._test_driver(op_type='symlink', initial_io=self._initial_io)
        redant.logger.info("Pass: Verification of gfid heal with "
                           "different file types after switching on "
                           "`self heal daemon` is complete when "
                           "symlink operations are performed")
