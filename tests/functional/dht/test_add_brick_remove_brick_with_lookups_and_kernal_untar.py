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

 Description:
    TC to check add-brick and remove-brick with lookups and kernel untar
"""

# disruptive;dist-rep,dist-disp
import traceback
from random import choice
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestAddBrickRemoveBrickWithlookupsAndKernaluntar(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        self.is_io_running = False
        self.list_of_io_processes = []

        # Check for 4 clients
        self.redant.check_hardware_requirements(clients=self.client_list,
                                                clients_count=4)

        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 3
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        for client in self.client_list:
            self.redant.execute_abstract_op_node(f"mkdir -p "
                                                 f"{self.mountpoint}",
                                                 client)
            self.redant.volume_mount(self.server_list[0], self.vol_name,
                                     self.mountpoint, client)

    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.list_of_io_processes, self.mounts)):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Enable brickmux on cluster, create a volume, start it and mount it.
        2. Start the below I/O from 4 clients:
           From client-1 : run script to create folders and files continuously
           From client-2 : start linux kernel untar
           From client-3 : while true;do find;done
           From client-4 : while true;do ls -lRt;done
        3. Kill brick process on one of the nodes.
        4. Add brick to the volume.
        5. Remove bricks from the volume.
        6. Validate if I/O was successful or not.
        """
        # Fill few bricks till it is full
        bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not bricks:
            raise Exception("Failed to get the bricks")

        # Create a dir to start untar
        self.linux_untar_dir = f"{self.mountpoint}/linuxuntar"
        redant.create_dir(self.mountpoint, "linuxuntar", self.client_list[0])

        # Start linux untar on dir linuxuntar
        proc = redant.run_linux_untar(self.client_list[0], self.mountpoint,
                                      dirs=tuple(['linuxuntar']))
        self.list_of_io_processes.append(proc[0])
        self.is_io_running = True
        self.mounts = [{
            "client": self.client_list[0],
            "mountpath": self.linux_untar_dir
        }]

        # Run script to create folders and files continuously
        proc = redant.create_deep_dirs_with_files(self.mountpoint, 758, 2,
                                                  100, 10, 105,
                                                  self.client_list[1])
        self.list_of_io_processes.append(proc)
        self.mounts.append({
            "client": self.client_list[1],
            "mountpath": self.mountpoint
        })

        # Run lookup operations from 2 clients
        cmd = (f"cd {self.mountpoint}; for i in `seq 1 10000`;"
               "do find .; done")
        proc = redant.execute_command_async(cmd, self.client_list[2])
        self.list_of_io_processes.append(proc)
        self.mounts.append({
            "client": self.client_list[2],
            "mountpath": self.mountpoint
        })

        cmd = f"cd {self.mountpoint}; for i in `seq 1 100000`;do ls -lRt;done"
        proc = redant.execute_command_async(cmd, self.client_list[3])
        self.list_of_io_processes.append(proc)
        self.mounts.append({
            "client": self.client_list[3],
            "mountpath": self.mountpoint
        })

        # Kill brick process of one of the nodes.
        brick = choice(bricks)
        node, _ = brick.split(":")
        ret = redant.kill_process(node, process_names="glusterfsd")
        if not ret:
            raise Exception(f"Failed to kill brick process of brick {brick}")

        # Add brick to volume
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick on volume {self.vol_name}")

        # Remove bricks from the volume
        ret = redant.shrink_volume(self.server_list[0], self.vol_name,
                                   rebal_timeout=2400)
        if not ret:
            raise Exception("Failed to remove-brick from volume")

        # Validate if I/O was successful or not.
        ret = redant.validate_io_procs(self.list_of_io_processes, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")
        self.is_io_running = False
