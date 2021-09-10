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

 Description:
    Test to verify heal on dispersed volume on file appends
"""

# disruptive;disp
from random import sample
from time import sleep
import traceback
from tests.d_parent_test import DParentTest


class TestHealOnFileAppends(DParentTest):

    def terminate(self):
        """
        Kill the IO on client
        """
        try:
            if self.is_io_started:
                ret = self.redant.kill_process(self.client_list[0],
                                               process_names=self.file_name)
                if not ret:
                    raise Exception("Failed to kill the process")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test steps:
        - create and mount EC volume 4+2
        - start append to a file from client
        - bring down one of the bricks (say b1)
        - wait for ~minute and bring down another brick (say b2)
        - after ~minute bring up first brick (b1)
        - check the xattrs 'ec.size', 'ec.version'
        - xattrs of online bricks should be same as an indication to heal
        """
        self.is_io_started = False
        self.file_name = 'test_file'

        # Get bricks list
        bricks_list = redant.get_all_bricks(self.vol_name,
                                            self.server_list[0])
        if not bricks_list:
            raise Exception('Not able to get bricks list')

        # Creating a file, generate and append data to the file
        cmd = (f"cd {self.mountpoint} ; while true; do "
               "cat /dev/urandom | tr -dc  [:space:][:print:] "
               f"| head -c 4K >> {self.file_name}; sleep 2; done;")
        proc = redant.execute_command_async(cmd, self.client_list[0])
        self.is_io_started = True

        # Select 3 bricks, 2 need to be offline and 1 will be healthy
        brick_1, brick_2, brick_3 = sample(bricks_list, 3)

        # Wait for IO to fill the bricks
        sleep(30)

        # Bring first brick offline and validate
        redant.bring_bricks_offline(self.vol_name, brick_1)
        ret = redant.are_bricks_offline(self.vol_name, brick_1,
                                        self.server_list[0])
        if not ret:
            raise Exception(f'Not able to validate brick {brick_1} being '
                            'offline')

        # Wait for IO to fill the bricks
        sleep(30)

        # Bring second brick offline and validate
        redant.bring_bricks_offline(self.vol_name, brick_2)
        ret = redant.are_bricks_offline(self.vol_name, brick_2,
                                        self.server_list[0])
        if not ret:
            raise Exception(f'Not able to validate brick {brick_2} being '
                            'offline')

        # Wait for IO to fill the bricks
        sleep(30)

        # Bring first brick online and validate peer status
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         brick_1)
        if not ret:
            raise Exception(f'Not able to bring brick {brick_1} '
                            'online')

        # To catchup onlined brick with healthy bricks
        sleep(30)

        # Validate the xattr to be same on onlined and healthy bric
        online_bricks = redant.get_online_bricks_list(self.vol_name,
                                                      self.server_list[0])
        if not online_bricks:
            raise Exception('Unable to fetch online bricks')

        for xattr in ('trusted.ec.size', 'trusted.ec.version'):
            ret = redant.validate_xattr_on_all_bricks([brick_1, brick_3],
                                                      self.file_name, xattr)
            if not ret:
                raise Exception(f"{xattr} is not same on all online bricks")

        # Get epoch time on the client
        ret = redant.execute_abstract_op_node('date +%s', self.client_list[0])
        prev_ctime = ret['msg'][0].strip()

        # Headroom for file ctime to get updated
        sleep(5)

        # Validate file was being apended while checking for xattrs
        ret = redant.get_file_stat(self.client_list[0],
                                   f"{self.mountpoint}/{self.file_name}")
        if not ret:
            raise Exception("Not able to get stat of the file")
        curr_ctime = ret['msg']['st_ctime']
        if int(curr_ctime) <= int(prev_ctime):
            raise Exception("Not able to validate data is appended to the "
                            "file while checking for xaatrs")
