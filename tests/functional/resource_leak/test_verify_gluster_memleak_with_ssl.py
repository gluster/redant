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
"""

# disruptive;dist-rep

from datetime import datetime, timedelta
import traceback
from tests.d_parent_test import DParentTest


class TestMemLeakAfterSSLEnabled(DParentTest):

    def terminate(self):
        """
        Check if memory logging and cpu usage running and
        If I/O processes are running wait from them to complete
        """
        try:
            if self.is_logging:
                ret = (self.redant.wait_for_logging_processes_to_stop(
                       self.monitor_proc_dict, cluster=True))
                if not ret:
                    raise Exception("ERROR: Failed to stop monitoring "
                                    "processes")
            if self.is_io_running:
                for proc in self.procs_list:
                    ret = self.redant.wait_till_async_command_ends(proc)
                    if ret['error_code'] != 0:
                        raise Exception("Failed to wait for I/O to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Steps:
        Scenario 1:
        1) Enable management encryption on the cluster.
        2) Create a 2X3 volume.
        3) Mount the volume using FUSE on a client node.
        4) Start doing IO on the mount (ran IO till the volume is ~88% full)
        5) Simultaneously start collecting the memory usage for
           'glusterfsd' process.
        6) Issue the command "# gluster v heal <volname> info" continuously
           in a loop.
        """
        self.is_io_running = False
        # Fill the vol approx 88%
        bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        usable_size = int(redant.get_usable_size_per_disk(bricks[0]) * 0.88)
        if not usable_size:
            raise Exception("Failed to get the usable size of the brick")
        self.procs_list = []
        counter = 1
        subvols_list = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols_list:
            redant.logger.error("No Sub-Volumes available for the volume "
                                f"{self.vol_name}")

        for _ in subvols_list:
            filename = f"{self.mountpoint}/test_file_{counter}"
            cmd = f"fallocate -l {usable_size}G {filename}"
            ret = redant.execute_command_async(cmd, self.client_list[0])
            self.procs_list.append(ret)
            counter += 1

        self.is_io_running = True
        # Start monitoring resource usage on servers and clients
        # default interval = 60 sec
        # count = 780 (60 *12)  => for 12 hrs
        self.is_logging = False

        # Start monitoring resource usage on servers and clients
        self.test_id = f"{self.test_name}-{self.volume_type}-logusage"
        self.monitor_proc_dict = (redant.log_memory_and_cpu_usage_on_cluster(
                                  self.server_list, self.client_list,
                                  self.test_id, count=780))
        if not self.monitor_proc_dict:
            raise Exception("Failed to start monitoring on servers and "
                            "clients")
        self.is_logging = True

        # Wait for I/O to complete and validate I/O on mount points
        for proc in self.procs_list:
            ret = redant.wait_till_async_command_ends(proc)
            if ret['error_code'] != 0:
                raise Exception("IO didn't complete or failed on client")
        self.is_io_running = False

        # Perform gluster heal info for 12 hours
        end_time = datetime.now() + timedelta(hours=12)
        while True:
            curr_time = datetime.now()
            cmd = f"gluster volume heal {self.vol_name} info"
            redant.execute_abstract_op_node(cmd, self.server_list[0])
            if curr_time > end_time:
                redant.logger.info("Successfully ran for 12 hours. Checking"
                                   "for memory leaks")
                break

        # Wait for monitoring processes to complete
        ret = redant.wait_for_logging_processes_to_stop(self.monitor_proc_dict,
                                                        cluster=True)
        if not ret:
            raise Exception("ERROR: Failed to stop monitoring processes")
        self.is_logging = False

        # Check if there are any memory leaks and OOM killers
        ret = (redant.check_for_memory_leaks_and_oom_kills_on_servers(
               self.test_id, self.server_list, self.vol_name))
        if ret:
            raise Exception("Memory leak and OOM kills check failed on"
                            " servers")

        ret = (redant.check_for_memory_leaks_and_oom_kills_on_clients(
               self.test_id, self.client_list))
        if ret:
            raise Exception("Memory leak and OOM kills check failed on"
                            " clients")
