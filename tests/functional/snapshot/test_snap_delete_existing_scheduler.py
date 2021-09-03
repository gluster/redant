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
    TC to validate snapshot scheduler behavior when existing schedule
    is deleted.
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
import traceback
from time import sleep
from tests.d_parent_test import DParentTest


class TestSnapshotDeleteExistingScheduler(DParentTest):

    def terminate(self):
        """
        Wait for IO to finish if the TC fails midway.
        Disable snap_scheduler and shared_storage
        """
        try:
            if self.is_io_running:
                io_ret = (self.redant.wait_for_io_to_complete(
                          self.all_mounts_procs, self.mounts))

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

            # Check if shared storage is enabled
            # Disable if true
            ret = self.redant.is_shared_volume_mounted(self.server_list)
            if ret:
                ret = self.redant.disable_shared_storage(self.server_list[0])
                if not ret:
                    shared_stor = False

            if not io_ret:
                raise Exception("Failed to wait for IO to complete")

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
        * Enable shared volume
        * Create a volume
        * Initialise snap_scheduler on all nodes
        * Enable snap_scheduler
        * Validate snap_scheduler status
        * Perform IO on mounts
        * Schedule a job of creating snapshot every 30 mins
        * Perform snap_scheduler list
        * Delete scheduled job
        * Validate IO is successful
        * Perform snap_scheduler list
        """
        self.is_io_running = False

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

        # Write files on all mounts
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            proc = redant.create_files('1k', {mount_obj['mountpath']},
                                       mount_obj['client'], 10, 'file')
            self.all_mounts_procs.append(proc)
            self.is_io_running = True

        # Add a job to schedule snapshot every 30 mins
        self.scheduler = r"*/30 * * * *"
        self.job_name = "Job1"
        redant.scheduler_add_jobs(self.server_list[0], self.job_name,
                                  self.scheduler, self.vol_name)

        # Perform snap_scheduler list
        redant.scheduler_list(self.server_list[0])

        # Delete scheduled job
        redant.scheduler_delete(self.server_list[0], self.job_name)

        # Validate IO
        if not redant.validate_io_procs(self.all_mounts_procs, self.mounts):
            raise Exception("IO failed.")
        self.is_io_running = False

        # Perform snap_scheduler list (no active jobs should be present)
        ret = redant.scheduler_list(self.server_list[0])
        out = ret['msg'][0].split(":")[1].strip()
        if out != "No snapshots scheduled":
            raise Exception("Unexpected: Jobs are getting listed even after "
                            "being deleted")
