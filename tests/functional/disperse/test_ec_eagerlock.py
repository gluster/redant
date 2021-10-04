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

Test Description:
    Verify Eagerlock and other-eagerlock behavior
"""
# disruptive;disp,dist-disp
from random import choice
from time import sleep
from copy import deepcopy
from datetime import datetime, timedelta
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Check for 4 clients
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=4)

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots, True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node("mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)
            self.redant.execute_abstract_op_node("yum -y install time",
                                                 client)

    def _filecreate_and_hashcheck(self, timeoutval):
        """Create a file and check on which subvol it is hashed to"""
        # Create and write to a file to test the eagerlock timeout behavior
        objectname = 'EagerLockTimeoutCheck-file-' + timeoutval
        objectpath = f"{self.mountpoint}/{objectname}"
        ret = self.redant.append_string_to_file(self.client_list[0],
                                                objectpath,
                                                'EagerLockTest')
        if not ret:
            raise Exception("Failed to append string to file")

        # Find the hashed subvol of the file created
        ret = self.redant.get_subvols(self.vol_name, self.server_list[0])
        if len(ret) > 1:
            hashed_subvol = self.redant.find_hashed_subvol(ret, '',
                                                           objectname)
            if hashed_subvol is None:
                self.redant.logger.error("Error in finding hash value")
                return None

            return (objectname, ret, hashed_subvol[1])

        # Set subvol to 0 for plain(non-distributed) disperse volume
        hashed_subvol = 0
        return (objectname, ret, hashed_subvol)

    def _get_dirty_xattr_value(self, subvol, hashed_subvol, filename):
        """Get trusted.ec.dirty xattr value to validate eagerlock behavior
        """
        # Collect ec.dirty xattr value from each brick
        result = []
        for brick in subvol[hashed_subvol]:
            host, brickpath = brick.split(':')
            brickpath = f"{brickpath}/{filename}"
            ret = (self.redant.get_extended_attributes_info(host, brickpath,
                   encoding='hex', attr_name='trusted.ec.dirty'))
            if not ret:
                continue
            ret = ret[brickpath]['trusted.ec.dirty']
            result.append(ret)

        # Check if xattr values are same across all bricks
        if result.count(result[0]) == len(result):
            return ret
        self.redant.logger.error("trusted.ec.dirty value is not consistent "
                                 "across the "
                                 f"disperse set {result}")
        return None

    def _change_eagerlock_timeouts(self, timeoutval):
        """Change eagerlock and other-eagerlock timeout values as per input"""
        options = {'disperse.eager-lock-timeout': timeoutval,
                   'disperse.other-eager-lock-timeout': timeoutval}
        self.redant.set_volume_options(self.vol_name, options,
                                       self.server_list[0])

    def _file_dir_create(self):
        """Create Directories and files which will be used for
        checking response time of lookups"""
        client = choice(self.client_list)
        proc = self.redant.create_deep_dirs_with_files(self.mountpoint,
                                                       0, 2, 4, 4, 100,
                                                       client)
        ret = self.redant.wait_till_async_command_ends(proc)
        if ret['error_code'] != 0:
            raise Exception("FAILED to create data needed for lookups")

    def _lookup_response_time(self):
        """ Check lookup response time which should be around 2-3 sec """
        # Sleeping to allow some cache timeout
        sleep(60)
        result = []
        for client in self.client_list:
            start_time = datetime.now().replace(microsecond=0)
            cmd = f"ls -lRt {self.mountpoint} >> /dev/null"
            end_time = datetime.now().replace(microsecond=0)
            self.redant.execute_abstract_op_node(cmd, client)
            result.append(end_time - start_time)

        # Checking the actual time taken for lookup
        for value in result:
            if value > timedelta(seconds=2):
                raise Exception("lookups taking more than 2 seconds."
                                f" Actual time: {value}")

    def _rmdir_on_mountpoint(self):
        """ Perform rm of created files as part of Sanity Check """
        # Skipping below lines of code as running rm -rf parallely
        # from multiple clients is a known bug Refer BZ-1787328
        # cmd = 'rm -rf ' + mountpoint
        # results = g.run_parallel(clients, cmd)
        # for client, ret_values in results.items():
        #    ret, out, err = ret_values
        #    self.assertEqual(ret, 0, "rm -rf failed on %s with %s"
        #                     % (client, err))

        cmd = f"rm -rf {self.mountpoint}/*"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def run_test(self, redant):
        """
        Test Steps:
        1) Create an ecvolume
        2) Test EagerLock and Other-EagerLock default values and timeout-values
        3) Set the timeout values to 60
        4) Write to a file and check backend brick for
        "trusted.ec.dirty=0x00000000000000000000000000000000", must be non-zero
        5) Create some  dirs and  files in each dir
        6) Do ls -lRt * --> must not take more than 2-3sec
        7) disable eager lock
        8) retest write to a file and this time lock must be released
           immediately with dirty.xattr value all zeros
        """
        # Set EC Eagerlock options to correct values
        options = {'disperse.eager-lock': 'on',
                   'disperse.eager-lock-timeout': '1',
                   'disperse.other-eager-lock': 'on',
                   'disperse.other-eager-lock-timeout': '1'}

        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0], True)

        # Test behavior with default timeout value of 1sec
        objectname, subvol, hashed_subvol = \
            self._filecreate_and_hashcheck('1sec')
        sleep(2)

        ret = self._get_dirty_xattr_value(subvol, hashed_subvol, objectname)
        if ret != '0x00000000000000000000000000000000':
            raise Exception("Unexpected dirty xattr value is set: "
                            f"{ret} on {objectname}")

        self._file_dir_create()

        # Now test the performance issue wrt lookups
        self._lookup_response_time()

        # Do rm -rf of created data as sanity test
        self._rmdir_on_mountpoint()

        # Increasing timeout values to 60sec in order to test the functionality
        self._change_eagerlock_timeouts('60')

        self._file_dir_create()

        objectname, subvol, hashed_subvol = \
            self._filecreate_and_hashcheck('60seconds')
        # Check in all the bricks "trusted.ec.dirty" value
        # It should be "0x00000000000000010000000000000001"
        ret = self._get_dirty_xattr_value(subvol, hashed_subvol, objectname)

        # Sleep 60sec after which dirty_val should reset to "0x00000..."
        sleep(62)

        ret = self._get_dirty_xattr_value(subvol, hashed_subvol, objectname)
        if ret != '0x00000000000000000000000000000000':
            raise Exception("Unexpected dirty xattr value is set: "
                            f"{ret} on {objectname}")

        # Test the performance issue wrt lookups
        self._lookup_response_time()

        # Do rm -rf of created data as sanity test
        self._rmdir_on_mountpoint()

        # Disable EagerLock and other-Eagerlock
        options = {'disperse.eager-lock': 'off',
                   'disperse.other-eager-lock': 'off'}
        redant.set_volume_options(self.vol_name, options,
                                  self.server_list[0], True)

        # Again create same dataset and retest ls -lRt, shouldnt take much time
        self._file_dir_create()

        # Create a new file see the dirty flag getting unset immediately
        objectname, subvol, hashed_subvol = \
            self._filecreate_and_hashcheck('Eagerlock_Off')

        # Check in all the bricks "trusted.ec.dirty value"
        # It should be "0x00000000000000000000000000000000"
        ret = self._get_dirty_xattr_value(subvol, hashed_subvol, objectname)
        if ret != '0x00000000000000000000000000000000':
            raise Exception("Unexpected dirty xattr value is set: "
                            f"{ret} on {objectname}")

        # Test the performance issue wrt ls
        self._lookup_response_time()

        # Cleanup created data as sanity test
        self._rmdir_on_mountpoint()
