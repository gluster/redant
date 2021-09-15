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

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Description:
    Test Disperse Quorum Count Set to 5
"""

# disruptive;disp,dist-disp
import traceback
from random import choice, sample
from tests.d_parent_test import DParentTest


class TestEcQuorumCount5(DParentTest):

    def terminate(self):
        """
        Wait for IOs to complete if the TC fails midway
        """
        try:
            _write_rc = False
            if self.is_write_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.procwrite, self.mounts)):
                    _write_rc = True

            _read_rc = False
            if self.is_read_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.procread, self.mount[1])):
                    _read_rc = True

            if _write_rc:
                raise Exception("Failed to wait for write IO to complete")
            if _read_rc:
                raise Exception("Failed to wait for read IO to complete")

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _generate_read_cmd(self, mountpoint, start, end):
        """Function which generates readcmd"""
        self.readcmd = (f"cd {mountpoint}; for i in `seq {start} {end}` ;"
                        "do dd if=file$i of=/dev/null bs=1M count=5;done")

    def run_test(self, redant):
        """
        Test Steps:
        - Write IO's when all bricks are online
        - Get subvol from which bricks to be brought down
        - Set volume disperse quorum count to 5
        - Start writing and reading IO's
        - Bring a brick down,say b1
        - Validate write and read is successful
        - Bring a brick down,say b2
        - Validate write has failed and read is successful
        - Start IO's again while quorum is not met on volume
          write should fail and read should pass
        - Add-brick and log
        - Start Rebalance
        - Wait for rebalance,which should fail as quorum is not met
        - Bring brick online
        - Wait for brick to come online
        - Check if bricks are online
        - Start IO's again when all bricks are online
        - IO's should complete successfully
        - Start IO's again and reset volume
        - Bring down other bricks to max redundancy
        - Validating IO's and waiting to complete
        """
        self.is_write_running = False
        self.is_read_running = False

        # Check if 2 clients are available in the cluster
        redant.check_hardware_requirements(clients=self.client_list,
                                           clients_count=2)

        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        client1 = self.mounts[0]['client']
        client2 = self.mounts[1]['client']

        # Write IO's  when all bricks are online
        writecmd = (f"cd {self.mountpoint}; for i in `seq 1 100` ;"
                    "do dd if=/dev/urandom of=file$i bs=1M count=5;done")

        # IO's should complete successfully
        redant.execute_abstract_op_node(writecmd, client1)

        # Select a subvol from which bricks to be brought down
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols list")
        bricks_list1 = list(choice(subvols))
        brick_1, brick_2 = sample(bricks_list1, 2)

        # Set volume disperse quorum count to 5
        options = {"disperse.quorum-count": "5"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        # Start writing and reading IO's
        self.procwrite, self.procread, count = [], [], 1
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 5, 10, 2, 15,
                                                      mount_obj['client'])
            self.procwrite.append(proc)
            count += 10
        self.is_write_running = True

        self._generate_read_cmd(self.mountpoint, 1, 10)
        proc = redant.execute_command_async(self.readcmd, client2)
        self.procread.append(proc)
        self.is_read_running = True

        # Brick 1st brick down
        ret = redant.bring_bricks_offline(self.vol_name, brick_1)
        if not ret:
            raise Exception(f'Brick {brick_1} is not offline')

        writecmd = (f"cd {self.mountpoint}; for i in `seq 101 110` ;"
                    "do dd if=/dev/urandom of=file$i bs=1M "
                    "count=5;done")

        # IO's should complete successfully
        redant.execute_abstract_op_node(writecmd, client1)

        self._generate_read_cmd(self.mountpoint, 101, 110)
        redant.execute_abstract_op_node(self.readcmd, client1)

        # Brick 2nd brick down
        ret = redant.bring_bricks_offline(self.vol_name, brick_2)
        if not ret:
            raise Exception(f'Brick {brick_2} is not offline')

        # Validate write has failed and read is successful
        ret = redant.validate_io_procs(self.procwrite, self.mounts)
        if ret:
            raise Exception('Write successful even after disperse quorum is '
                            'not met')
        self.is_write_running = False

        ret = redant.validate_io_procs(self.procread, self.mounts[1])
        if not ret:
            raise Exception('Read operation failed on the client')
        self.is_read_running = False

        # Start IO's again while quorum is not met on volume
        self.procwrite = []
        proc = redant.create_deep_dirs_with_files(self.mountpoint, 20, 1, 10,
                                                  1, 10, client1)
        self.procwrite.append(proc)

        ret = redant.validate_io_procs(self.procwrite, self.mounts[0])
        if ret:
            raise Exception('Write successful even after disperse quorum is '
                            'not met')

        self._generate_read_cmd(self.mountpoint, 1, 100)
        redant.execute_abstract_op_node(self.readcmd, client2)

        # Add brick
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots,
                                   force=True)
        if not ret:
            raise Exception(f"Failed to expand the volume {self.vol_name}")

        # Log Volume Info and Status after expanding the volume
        if not (self.redant.log_volume_info_and_status(self.server_list[0],
                self.vol_name)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.vol_name}")

        # Start Rebalance
        redant.rebalance_start(self.vol_name, self.server_list[0])

        # Wait for rebalance to complete
        # Which should also fail as quorum is not met
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=600)
        if ret:
            raise Exception("Rebalance passed though disperse quorum "
                            "is not met on volume")

        # Bring brick online
        brick_list = [brick_1, brick_2]
        ret = redant.bring_bricks_online(self.vol_name, self.server_list,
                                         brick_list)
        if not ret:
            raise Exception('Brick not brought online')

        # Wait for brick to come online
        ret = redant.wait_for_bricks_to_come_online(self.vol_name,
                                                    self.server_list,
                                                    brick_list)
        if not ret:
            raise Exception('Bricks are not online')

        # Check if bricks are online
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])
        ret = redant.are_bricks_online(self.vol_name, all_bricks,
                                       self.server_list[0])
        if not ret:
            raise Exception('All bricks are not online')

        # Start IO's again when all bricks are online
        writecmd = (f"cd {self.mountpoint}; for i in `seq 101 200` ;"
                    "do dd if=/dev/urandom of=file$i bs=1M "
                    "count=5;done")

        self._generate_read_cmd(self.mountpoint, 101, 120)

        # IO's should complete successfully
        redant.execute_abstract_op_node(writecmd, client1)

        redant.execute_abstract_op_node(self.readcmd, client2)

        # Start IO's again
        self.procwrite, count = [], 30
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 10, 2, 5,
                                                      mount_obj['client'])
            self.procwrite.append(proc)
            count += 10
        self.is_write_running = True

        # Reset volume
        redant.volume_reset(self.vol_name, self.server_list[0])

        # Bring down other bricks to max redundancy
        # Bringing bricks offline
        bricks_to_offline = sample(bricks_list1, 2)
        ret = redant.bring_bricks_offline(self.vol_name, bricks_to_offline)
        if not ret:
            raise Exception('Redundant bricks not offline')

        # Validating IO's and waiting to complete
        ret = redant.validate_io_procs(self.procwrite, self.mounts)
        if not ret:
            raise Exception('IO failed on some of the clients')
        self.is_write_running = False
