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

# disruptive;arb,dist,rep,disp,dist-arb,dist-rep,dist-disp
import traceback
from tests.d_parent_test import DParentTest


class TestBasicMemoryleak(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Check clients configuration
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=2)

        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0],
                                     self.vol_name,
                                     self.mountpoint, client)
        self.is_io_running = False

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
        2. Start I/O from mount point.
        3. Check if there are any memory leaks and OOM killers.
        """
        self.is_logging = False
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

        # Start monitoring resource usage on servers and clients
        self.test_id = f"{self.test_name}-{self.volume_type}-logusage"
        self.monitor_proc_dict = (redant.log_memory_and_cpu_usage_on_cluster(
                                  self.server_list, self.client_list,
                                  self.test_id, count=30))
        if not self.monitor_proc_dict:
            raise Exception("Failed to start monitoring on servers and "
                            "clients")
        self.is_logging = True

        # Start multiple I/O from mount points
        self.is_io_running = True
        self.procs_list = []
        cmd = (f"cd {self.mountpoint};for i in `seq 1 100`; do mkdir dir.$i;"
               "for j in `seq 1 1000`; do dd if=/dev/random "
               "of=dir.$i/testfile.$j bs=1k count=10;done;done")
        ret = redant.execute_command_async(cmd, self.client_list[0])
        self.procs_list.append(ret)

        # Create a dir to start untar
        redant.create_dir(self.mountpoint, "linuxuntar", self.client_list[1])

        # Start linux untar on dir linuxuntar
        proc = redant.run_linux_untar(self.client_list[1], self.mountpoint,
                                      dirs=tuple(['linuxuntar']))
        self.procs_list.append(proc[0])

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

        ret = (redant.check_for_memory_leaks_and_oom_kills_on_clients(
               self.test_id, self.client_list))
        if ret:
            raise Exception("Memory leak and OOM kills check failed on"
                            " clients")
