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

# disruptive;arb,rep,disp,dist-arb,dist-rep,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestMemoryLeakInShdWithCacheInvalidationOn(DParentTest):

    def terminate(self):
        """
        Check if memory logging and cpu usage
        """
        try:
            if self.is_logging:
                ret = (self.redant.wait_for_logging_processes_to_stop(
                       self.monitor_proc_dict, cluster=True))
                if not ret:
                    raise Exception("ERROR: Failed to stop monitoring "
                                    "processes")
            if self.is_io_running:
                if not self.redant.wait_for_io_to_complete(self.procs_list,
                                                           self.mounts):
                    raise Exception("Failed to wait for I/O to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Set features.cache-invalidation to ON.
        3. Start I/O from mount point.
        4. Run gluster volume heal command in a loop
        5. Check if there are any memory leaks and OOM killers on servers.
        """
        self.is_io_running = False
        self.is_logging = False
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Start monitoring resource usage on servers and clients
        self.test_id = f"{self.test_name}-{self.volume_type}-logusage"
        self.monitor_proc_dict = (redant.log_memory_and_cpu_usage_on_cluster(
                                  self.server_list, self.client_list,
                                  self.test_id, count=10))
        if not self.monitor_proc_dict:
            raise Exception("Failed to start monitoring on servers and "
                            "clients")
        self.is_logging = True

        # Set features.cache-invalidation to ON
        redant.set_volume_options(self.vol_name,
                                  {'features.cache-invalidation': 'on'},
                                  self.server_list[0])

        # Start multiple I/O from mount points
        self.procs_list = []
        cmd = (f"cd {self.mountpoint};for i in `seq 1 1000`;"
               "do echo 'abc' > myfile;done")
        ret = redant.execute_command_async(cmd, self.client_list[0])
        self.procs_list.append(ret)
        self.is_io_running = True

        # Run gluster volume heal command in a loop for 100 iterations
        for _ in range(0, 100):
            if not redant.trigger_heal(self.vol_name, self.server_list[0]):
                raise Exception("Starting heal failed")

        # Wait for I/O to complete and validate I/O on mount points
        if not redant.validate_io_procs(self.procs_list, self.mounts):
            raise Exception("IO didn't complete or failed on client")
        self.is_io_running = False

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
