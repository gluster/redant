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

# disruptive;arb,dist-arb
import traceback
from tests.d_parent_test import DParentTest


class TestCase(DParentTest):

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
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Create a volume, start it and mount it.
        2. Create 10,000 files each of size 200K
        3. Delete the files created at step 2
        4. Check if the files are deleted from backend
        5. Check if there are any memory leaks and OOM killers.
        """
        self.is_logging = False
        # Start monitoring resource usage on servers and clients
        self.test_id = f"{self.test_name}-{self.volume_type}-logusage"
        self.monitor_proc_dict = (redant.log_memory_and_cpu_usage_on_cluster(
                                  self.server_list, self.client_list,
                                  self.test_id, count=30))
        if not self.monitor_proc_dict:
            raise Exception("Failed to start monitoring on servers and "
                            "clients")

        self.is_logging = True
        # Create files on mount point
        cmd = (f'cd {self.mountpoint};for i in {{1..10000}};'
               'do dd if=/dev/urandom bs=200K count=1 of=file$i;done;'
               f'rm -rf {self.mountpoint}/file*')
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Delete files from mount point and check if all files
        # are deleted or not from mount point as well as backend bricks.
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        ret = redant.get_dir_contents(self.mountpoint, self.client_list[0])
        if ret:
            raise Exception("Mountpoint is not empty")

        for brick in redant.get_all_bricks(self.vol_name, self.server_list[0]):
            node, brick_path = brick.split(":")
            ret = redant.get_dir_contents(brick_path, node)
            if ret:
                raise Exception("Bricks are not empty")

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
