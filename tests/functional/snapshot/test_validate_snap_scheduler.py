"""
 Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>

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
    TC to validate snapshot scheduler behaviour when we enable/disable
    scheduler.
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestSnapshotSchedulerBehaviour(DParentTest):

    def terminate(self):
        """
        Disable snap_scheduler (if TC failed midway)
        and shared_storage
        """
        try:
            snap_stat = True
            if self.is_scheduler_enabled:
                # Disable snap scheduler
                self.redant.scheduler_disable(self.server_list[0], False)

                # Check snapshot scheduler status
                for server in self.server_list:
                    count = 0
                    while count < 40:
                        ret = self.redant.scheduler_status(server, False)
                        status = ret['msg'][0].split(':')
                        if len(status) == 3:
                            status = status[2].strip()
                            if ret['error_code'] == 0 \
                               and status == "Disabled":
                                break
                        sleep(2)
                        count += 1
                    if ret['error_code'] != 0:
                        snap_stat = False

            shared_stor = True
            # Check if shared storage is enabled
            # Disable if true
            ret = self.redant.is_shared_volume_mounted(self.server_list)
            if ret:
                ret = self.redant.disable_shared_storage(self.server_list[0])
                if not ret:
                    shared_stor = False

            if not snap_stat:
                raise Exception("Failed to check status of scheduler")

            if not shared_stor:
                raise Exception("Failed to disable shared storage")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        1. Create volumes
        2. Enable shared storage
        3. Validate shared storage mounted
        4. Validate shared storage is enabled
        5. Initialise snapshot scheduler on all node
        6. Enable snapshot scheduler
        7. Validate snapshot scheduler status
        8. Disable snapshot scheduler
        9. Validate snapshot scheduler status
        """
        self.is_scheduler_enabled = False

        # Enable shared storage
        ret = redant.enable_shared_storage(self.server_list[0])
        if not ret:
            raise Exception("Failed to enable shared storage")

        # Validate shared storage volume is mounted
        ret = redant.is_shared_volume_mounted(self.server_list[0], timeout=10)
        if not ret:
            raise Exception("Failed to validate if shared volume is mounted")

        # Initialise snap scheduler
        count = 0
        sleep(2)
        while count < 40:
            ret = redant.scheduler_init(self.server_list)
            if ret:
                break
            sleep(2)
            count += 1
        if not ret:
            raise Exception("Failed to initialize scheduler on all nodes")

        # Enable snap scheduler
        redant.scheduler_enable(self.server_list[0])
        self.is_scheduler_enabled = True

        # Validate snapshot scheduler status
        for server in self.server_list:
            count = 0
            while count < 40:
                ret = redant.scheduler_status(server, False)
                status = ret['msg'][0].split(':')
                if len(status) == 3:
                    status = status[2].strip()
                    if ret['error_code'] == 0 and status == "Enabled":
                        break
                sleep(2)
                count += 1
            if ret['error_code'] != 0:
                raise Exception("Failed to check status of scheduler"
                                f" on node {server}")

        # Disable snap scheduler
        self.redant.scheduler_disable(self.server_list[0], False)

        # Check snapshot scheduler status
        for server in self.server_list:
            count = 0
            while count < 40:
                ret = self.redant.scheduler_status(server, False)
                status = ret['msg'][0].split(':')
                if len(status) == 3:
                    status = status[2].strip()
                    if ret['error_code'] == 0 \
                       and status == "Disabled":
                        break
                sleep(2)
                count += 1
            if ret['error_code'] != 0:
                raise Exception("Failed to check status of scheduler"
                                f" on node {server}")
        self.is_scheduler_enabled = False
