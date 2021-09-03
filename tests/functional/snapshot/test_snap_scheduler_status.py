"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to verify the snap_scheduler functionality WRT the status
    and shared storage
"""

# disruptive;rep,dist-rep,disp,dist,dist-disp
import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestSnapshotSchedulerStatus(DParentTest):

    def terminate(self):
        """
        Disable shared storage and snap_scheduler
        """
        try:
            # Disable snap scheduler
            self.redant.scheduler_disable(self.server_list[0], False)

            # Check snapshot scheduler status
            for server in self.server_list:
                count = 0
                while count < 40:
                    ret = self.redant.scheduler_status(server, False)
                    if ret['error_code'] != 0:
                        break
                    # status = status.strip().split(":")[2]
                    # if ret == 0 and status == ' Enabled':
                    #     break
                    sleep(2)
                    count += 1
                if ret['error_code'] == 0:
                    raise Exception("Unexpected: Status of scheduler"
                                    f" on node {server} was successfull")

            # Check if shared storage is enabled
            # Disable if true
            ret = self.redant.is_shared_volume_mounted(self.server_list)
            if ret:
                ret = self.redant.disable_shared_storage(self.server_list[0])
                if not ret:
                    raise Exception("Failed to disable shared storage")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        * Initialise snap_scheduler without enabling shared storage
        * Enable shared storage
        * Initialise snap_scheduler on all nodes
        * Check snap_scheduler status
        """
        # Validate shared storage is disabled
        option = "cluster.enable-shared-storage"
        volinfo = redant.get_volume_options(self.vol_name, option,
                                            self.server_list[0])
        if volinfo["cluster.enable-shared-storage"] == "disable":
            # Initialise snapshot scheduler
            ret = redant.scheduler_init(self.server_list)
            if ret:
                raise Exception("Unexpected: Successfully initialized "
                                "scheduler on all nodes")
        else:
            raise Exception("Unexpected: Shared storage enabled on cluster")

        # Enable shared storage
        ret = redant.enable_shared_storage(self.server_list[0])
        if not ret:
            raise Exception("Failed to enable shared storage")

        # Validate shared storage volume is mounted
        ret = redant.is_shared_volume_mounted(self.server_list[0], timeout=10)
        if not ret:
            raise Exception("Failed to validate if shared volume is mounted")

        # Validate shared storage volume is enabled
        option = "cluster.enable-shared-storage"
        volinfo = redant.get_volume_options(self.vol_name, option,
                                            self.server_list[0])
        if volinfo["cluster.enable-shared-storage"] != "enable":
            raise Exception("Failed to validate if shared storage is enabled")

        # Initialise snap_scheduler on all nodes
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

        # Enable snap_scheduler
        redant.scheduler_enable(self.server_list[0])

        # Check snapshot scheduler status
        for server in self.server_list:
            count = 0
            while count < 40:
                ret = redant.scheduler_status(server, False)
                if ret['error_code'] == 0:
                    break
                # status = status.strip().split(":")[2]
                # if ret == 0 and status == ' Enabled':
                #     break
                sleep(2)
                count += 1
            if ret['error_code'] != 0:
                raise Exception("Failed to check status of scheduler"
                                f" on node {server}")
