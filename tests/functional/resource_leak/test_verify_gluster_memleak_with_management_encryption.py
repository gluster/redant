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


class TestMemLeakAfterMgmntEncrypEnabled(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = self.vol_type_inf[self.volume_type]
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

        # Disable I/O encryption
        self._disable_io_encryption()

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

    def _run_io(self):
        """ Run IO and fill vol upto ~88%"""
        bricks = self.redant.get_all_bricks(self.vol_name, self.server_list[0])
        usable_size = (int(self.redant.get_usable_size_per_disk(
                       bricks[0]) * 0.88))
        if not usable_size:
            raise Exception("Failed to get the usable size of the brick")

        self.procs_list = []
        counter = 1
        subvols_list = self.redant.get_subvols(self.vol_name,
                                               self.server_list[0])
        if not subvols_list:
            self.redant.logger.error("No Sub-Volumes available for the "
                                     f"volume {self.vol_name}")

        for _ in subvols_list:
            filename = f"{self.mountpoint}/test_file_{counter}"
            cmd = f"fallocate -l {usable_size}G {filename}"
            ret = self.redant.execute_command_async(cmd, self.client_list[0])
            self.procs_list.append(ret)
            counter += 1

    def _perform_gluster_v_heal_for_12_hrs(self):
        """ Run 'guster v heal info' for 12 hours"""
        # Perform gluster heal info for 12 hours
        end_time = datetime.now() + timedelta(hours=12)
        while True:
            curr_time = datetime.now()
            cmd = f"gluster volume heal {self.vol_name} info"
            self.redant.execute_abstract_op_node(cmd, self.server_list[0])
            if curr_time > end_time:
                self.redant.logger.info("Successfully ran for 12 hours."
                                        " Checking for memory leaks")
                break

    def _verify_memory_leak(self):
        """ Verify memory leak is found """
        ret = (self.redant.check_for_memory_leaks_and_oom_kills_on_servers(
               self.test_id, self.server_list, self.vol_name))
        if ret:
            raise Exception("Memory leak and OOM kills check failed on"
                            " servers")

        ret = (self.redant.check_for_memory_leaks_and_oom_kills_on_clients(
               self.test_id, self.client_list))
        if ret:
            raise Exception("Memory leak and OOM kills check failed on"
                            " clients")

    def _disable_io_encryption(self):
        """ Disables IO encryption """
        # UnMount Volume
        self.redant.volume_unmount(self.vol_name, self.mountpoint,
                                   self.client_list[0])

        # Stop Volume
        self.redant.volume_stop(self.vol_name, self.server_list[0])

        # Disable server and client SSL usage
        options = {"server.ssl": "off",
                   "client.ssl": "off"}
        self.redant.set_volume_options(self.vol_name, options,
                                       self.server_list[0], True)

        # Start Volume
        self.redant.volume_start(self.vol_name, self.server_list[0])

        # Mount Volume
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def run_test(self, redant):
        """
        CASE 1- test_mem_leak_on_gluster_procs_with_management_encrpytion
        Steps:
        1) Enable management encryption on the cluster.
        2) Create a 2X3 volume.
        3) Mount the volume using FUSE on a client node.
        4) Start doing IO on the mount (ran IO till the volume is ~88% full)
        5) Simultaneously start collecting the memory usage for
           'glusterfsd' process.
        6) Issue the command "# gluster v heal <volname> info" continuously
           in a loop.
        """
        # Run IO
        self.is_io_running = False
        self._run_io()
        self.is_io_running = True

        # Start monitoring resource usage on servers and clients
        # default interval = 60 sec, count = 780 (60 *12)  => for 12 hrs
        self.is_logging = False
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)

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
        if not redant.validate_io_procs(self.procs_list, self.mounts):
            raise Exception("IO didn't complete or failed on client")
        self.is_io_running = False

        self._perform_gluster_v_heal_for_12_hrs()

        # Wait for monitoring processes to complete
        ret = redant.wait_for_logging_processes_to_stop(self.monitor_proc_dict,
                                                        cluster=True)
        if not ret:
            raise Exception("ERROR: Failed to stop monitoring processes")
        self.is_logging = False

        # Check if there are any memory leaks and OOM killers
        self._verify_memory_leak()

        # Cleanup volumes for next TC
        redant.cleanup_volumes(self.server_list, self.vol_name)

        # Setup the volume again
        conf_hash = self.vol_type_inf[self.volume_type]
        redant.setup_volume(self.vol_name, self.server_list[0],
                            conf_hash, self.server_list,
                            self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                        self.client_list[0])
        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        """
        CASE 2- test_mem_leak_on_gluster_procs_with_brick_multiplex
        Steps:
        1) Enable cluster.brick-multiplex
        2) Enable SSL on management layer
        3) Start creating volumes
        4) Mount a volume and starting I/O
        5) Monitor the memory consumption by glusterd process
        """
        # Enable cluster.brick-mulitplex
        if not redant.is_brick_mux_enabled(self.server_list[0]):
            if not redant.enable_brick_mux(self.server_list[0]):
                raise Exception("Failed to enable brick multiplexing")

        # Verify the operation
        if not redant.is_brick_mux_enabled(self.server_list[0]):
            raise Exception("Brick multiplexing status is not enable")

        # Create few volumes
        conf_dict = self.vol_type_inf['dist-rep']
        redant.bulk_volume_creation(self.server_list[0], 100, self.vol_name,
                                    conf_dict, self.server_list,
                                    self.brick_roots, force=True)

        # Run IO
        self.is_io_running = False
        self._run_io()
        self.is_io_running = True

        # Start memory usage logging
        self.test_id = f"{self.test_name}-{self.volume_type}-logusage"
        self.monitor_proc_dict = (redant.log_memory_and_cpu_usage_on_cluster(
                                  self.server_list, self.client_list,
                                  self.test_id, count=60))
        if not self.monitor_proc_dict:
            raise Exception("Failed to start monitoring on servers and "
                            "clients")
        self.is_logging = True

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
        self._verify_memory_leak()

        # Disable Brick multiplex
        if redant.is_brick_mux_enabled(self.server_list[0]):
            if not redant.disable_brick_mux(self.server_list[0]):
                raise Exception("Failed to disable brick multiplexing")
