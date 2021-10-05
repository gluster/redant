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
    Arbiter test writes and reads from a file
"""

# disruptive;arb,dist-arb

import traceback
from random import sample
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

    def terminate(self):
        """
        In case the test fails midway then wait for IO to complete before
        calling the terminate function of DParentTest
        """
        try:
            ret = self.redant.wait_for_io_to_complete(self.list_of_procs,
                                                      self.mnt_list)
            if not ret:
                raise Exception("IO failed on some of the clients")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _bring_bricks_online_heal(self, node: str, volname: str,
                                  bricks_list: list):
        """
        Bring bricks online and monitor heal completion
        """
        # Bring bricks online
        self.redant.bring_bricks_online(volname, self.server_list,
                                        bricks_list)
        if not self.redant.are_bricks_online(volname, bricks_list,
                                             node):
            raise Exception(f"Bricks {bricks_list} not online")

        # Wait for volume processes to be online
        if not (self.redant.
                wait_for_volume_process_to_be_online(volname, node,
                                                     self.server_list)):
            raise Exception(f"Failed to wait for volume {volname}"
                            " processes to be online")

        # Verify volume's all process are online
        if not (self.redant.
                verify_all_process_of_volume_are_online(volname, node)):
            raise Exception(f"Volume {volname} : All process are not online")

        # Monitor heal completion
        if not self.redant.monitor_heal_completion(node, volname):
            raise Exception('Heal has not yet completed')

        # Check for split-brain
        if self.redant.is_volume_in_split_brain(node, volname):
            raise Exception('Volume is in split-brain state')

    def run_test(self, redant):
        """
        Test read and write of file
        Description:
        - Get the bricks from the volume
        - Creating directory test_write_and_read_file
        - Write from 1st client
        - Read from 2nd client
        - Select brick to bring offline
        - Bring brick offline
        - Validating IO's on client1
        - Validating IO's on client2
        - Bring bricks online
        - Wait for volume processes to be online
        - Verify volume's all process are online
        - Monitor heal completion
        - Check for split-brain
        - Bring 2nd brick offline
        - Check if brick is offline
        - Write from 1st client
        - Read from 2nd client
        - Bring bricks online
        - Wait for volume processes to be online
        - Verify volume's all process are online
        - Monitor heal completion
        - Check for split-brain
        """

        self.list_of_procs = []
        # Get the bricks from the volume
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if bricks_list is None:
            raise Exception("Empty bricks list")

        # Creating directory test_write_and_read_file
        self.mnt_list = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        redant.create_dir(self.mnt_list[0]['mountpath'],
                          "test_write_and_read_file",
                          self.mnt_list[0]['client'])

        # Write from 1st client
        cmd_to_write = (f'cd {self.mnt_list[0]["mountpath"]}/'
                        'test_write_and_read_file ; for i in '
                        '`seq 1 5000` ;do echo -e "Date:`date`\n'
                        '" >> test_file ;echo -e "`cal`\n" >> test_file ;'
                        ' done ; cd ..')
        redant.logger.info(f"Executing {cmd_to_write} on "
                           f"{self.mnt_list[0]['client']}")
        proc1 = redant.execute_command_async(cmd_to_write,
                                             self.mnt_list[0]['client'])

        # Read from 2nd client
        cmd = (f'cd {self.mnt_list[1]["mountpath"]}/ ;'
               'for i in {1..30};do cat test_write_and_read_file/'
               'test_file;done')
        redant.logger.info(f"Executing {cmd} on "
                           f"{self.mnt_list[1]['client']}")
        proc2 = redant.execute_command_async(cmd,
                                             self.mnt_list[1]['client'])
        self.list_of_procs = [proc1, proc2]

        # Bring brick offline
        bricks_to_bring_offline = sample(bricks_list, 2)
        redant.bring_bricks_offline(self.vol_name,
                                    bricks_to_bring_offline[0])

        # Check brick is offline
        if not redant.are_bricks_offline(self.vol_name,
                                         [bricks_to_bring_offline[0]],
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline[0]} are "
                            "not offline")

        # Validating IO's
        for proc, mount in zip(self.list_of_procs, self.mnt_list):
            if not redant.validate_io_procs(proc, mount, timeout=1800):
                raise Exception("IO failed on some of the clients")

        self._bring_bricks_online_heal(self.server_list[0],
                                       self.vol_name, bricks_list)

        # Bring down second brick
        redant.bring_bricks_offline(self.vol_name,
                                    bricks_to_bring_offline[1])

        # Check if brick is offline
        if not redant.are_bricks_offline(self.vol_name,
                                         [bricks_to_bring_offline[1]],
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline[1]} are "
                            "not offline")

        # Write from 1st client
        redant.execute_abstract_op_node(cmd_to_write,
                                        self.mnt_list[0]['client'])
        # Read from 2nd client
        cmd = (f'cd {self.mnt_list[1]["mountpath"]}/'
               ' ;cat test_write_and_read_file/test_file')

        redant.execute_abstract_op_node(cmd,
                                        self.mnt_list[1]['client'])

        self._bring_bricks_online_heal(self.server_list[0],
                                       self.vol_name, bricks_list)
