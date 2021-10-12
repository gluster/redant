"""
 Copyright (C) 2021  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check split-brain on node reboot
"""

# disruptive;rep,dist-rep
import traceback
from tests.d_parent_test import DParentTest


class TestSelfHeal(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        # Check clients configuration
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=4)

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
        # If I/O processes are running wait from them to complete
        try:
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
        Steps:
        1. Create *3 replica volume
        2. Mount the volume on 3 clients
        3. Run following workload from clients
        Client 1: Linux Untars
        Client 2: Lookups ls
        Client 3: Lookups du
        Client 4: Create deep dirs and file
        6. Perform node reboot
        7. Check for heal status
        8. Reboot another node
        9. Check for heal status
        """
        self.procs_list = []
        # Create a dir to start untar
        redant.create_dir(self.mountpoint, "linuxuntar", self.client_list[0])

        # Start linux untar on dir linuxuntar from client 1
        proc = redant.run_linux_untar(self.client_list[0], self.mountpoint,
                                      dirs=tuple(['linuxuntar']))
        self.procs_list.append(proc[0])
        self.is_io_running = True

        # Run lookup operation ls from client 2
        cmd = f"cd {self.mountpoint};for i in `seq 1 1000000`;do du -sh; done"
        ret = redant.execute_command_async(cmd, self.client_list[1])
        self.procs_list.append(ret)

        # Run lookup operation du from client 3
        cmd = (f"cd {self.mountpoint}; for i in `seq 1 1000000`; do ls -laRt;"
               " done")
        ret = redant.execute_command_async(cmd, self.client_list[2])
        self.procs_list.append(ret)

        # Create a dir to start crefi tool
        self.crefi_dir = f"{self.mountpoint}/crefi"
        redant.create_dir(self.mountpoint, "crefi", self.client_list[3])

        # Create a deep-dirs on client 4
        list_of_fops = ("create", "rename", "chmod", "chown", "chgrp",
                        "hardlink", "truncate", "setxattr")
        for fops in list_of_fops:
            ret = redant.run_crefi(self.client_list[3],
                                   self.crefi_dir, 5, 2, 2, thread=4,
                                   random_size=True, fop=fops, minfs=0,
                                   maxfs=10240, multi=True,
                                   random_filename=True)
            if not ret:
                raise Exception(f"crefi failed during {fops}")

        for server_num in (1, 2):
            # Perform node reboot for servers
            if not redant.reboot_nodes(self.server_list[server_num]):
                raise Exception("Failed to reboot node")
            if not redant.wait_node_power_up(self.server_list[server_num]):
                raise Exception("Node not yet online after reboot")

            # Monitor heal completion
            if not redant.monitor_heal_completion(self.server_list[0],
                                                  self.vol_name):
                raise Exception("Heal has not yet completed")

            # Check if heal is completed
            if not redant.is_heal_complete(self.server_list[0],
                                           self.vol_name):
                raise Exception("Heal is not complete")
