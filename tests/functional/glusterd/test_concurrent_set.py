"""
  Copyright (C) 2016-2017  Red Hat, Inc. <http://www.redhat.com>

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
  Performing concurrent volume set operations on two
  different volumes and checking for existence os core file.
"""

import random
import traceback
from tests.nd_parent_test import NdParentTest


# nonDisruptive;dist
class TestCase(NdParentTest):

    def terminate(self):
        try:
            self.redant.cleanup_volume(self.server_list, self.volume_name1)
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        1) Create a distributed volume. Use both existing and
           created volumes for the operation.
        2) Form volume set command for both volumes.
        3) Execute the commands on both the volumes asyncronously.
        4) Check for the completion of the concurrent execution.
        5) Check for the core file creation in the end.
        """
        # time stamp of current test case
        ret = redant.execute_abstract_op_node('date +%s', self.server_list[0])
        timestamp = ret['msg'][0].rstrip("\n")

        # Create a volume
        volume_type1 = 'dist'
        self.volume_name1 = f"{self.test_name}-{volume_type1}-1"
        redant.volume_create(self.volume_name1, self.server_list[0],
                             self.vol_type_inf[volume_type1],
                             self.server_list, self.brick_roots, True)

        cmd1 = ("for i in `seq 1 100`; do gluster volume set "
                f"{self.vol_name} read-ahead on; done")
        cmd2 = ("for i in `seq 1 100`; do gluster volume set "
                f"{self.volume_name1} write-behind on; done")

        proc1 = redant.execute_command_async(cmd1,
                                             random.choice(self.server_list))
        proc2 = redant.execute_command_async(cmd2,
                                             random.choice(self.server_list))

        ret1 = redant.wait_till_async_command_ends(proc1)
        ret2 = redant.wait_till_async_command_ends(proc2)

        if ret1['error_code'] != 0:
            raise Exception("Concurrent volume set on different volumes "
                            "simultaneously failed")
        if ret2['error_code'] != 0:
            raise Exception("Concurrent volume set on different volumes "
                            "simultaneously failed")

        ret = redant.check_core_file_exists(self.server_list, timestamp)
        if not ret:
            redant.logger.info("No core file found, glusterd service "
                               "running successfully")
        else:
            raise Exception("core file found in directory, it "
                            "indicates the glusterd service crash")
