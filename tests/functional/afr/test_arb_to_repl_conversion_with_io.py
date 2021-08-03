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
    TC to perform a volume conversion from Arbiter to Replicated
    with background IOs
"""

# disruptive;arb,dist-arb
import traceback
from datetime import datetime, timedelta
from time import sleep
from tests.d_parent_test import DParentTest


class TestArbiterToReplicatedConversion(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete, if the TC fails.
        """
        try:
            if self.proc:
                if not self.redant.wait_for_io_to_complete(self.proc,
                                                           self.mounts):
                    raise Exception("Failed to wait for IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _get_arbiter_bricks(self):
        """
        Returns tuple of arbiter bricks from the volume
        """
        # Get all subvols
        subvols = self.redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception(f"Not able to get subvols of {self.vol_name}")

        # Last brick in every subvol will be the arbiter
        return tuple(zip(*subvols))[-1]

    def run_test(self, redant):
        """
        Steps:
        - Create, start and mount an arbiter volume in two clients
        - Create two dir's, fill IO in first dir and take note of arequal
        - Start a continuous IO from second directory
        - Convert arbiter to x2 replicated volume (remove brick)
        - Convert x2 replicated to x3 replicated volume (add brick)
        - Wait for ~5 min for vol file to be updated on all clients
        - Enable client side heal options and issue volume heal
        - Validate heal completes with no errors and arequal of first dir
          matches against initial checksum
        """
        # Fill IO in first directory
        cmd = ("python3 /tmp/file_dir_ops.py create_deep_dirs_with_files "
               "--dir-depth 10 --fixed-file-size 1M --num-of-files 100 "
               f"--dirname-start-num 1 {self.mountpoint}")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Take `arequal` checksum on first directory
        self.mounts = {
            'client': self.client_list[0],
            'mountpath': self.mountpoint
        }
        exp_arequal = redant.collect_mounts_arequal(self.mounts, "user1")

        # Start continuous IO from second directory
        cmd = ("python3 /tmp/file_dir_ops.py create_deep_dirs_with_files "
               "--dir-depth 10 --fixed-file-size 1M --num-of-files 250 "
               f"--dirname-start-num 2 {self.mountpoint}")
        self.proc = redant.execute_command_async(cmd, self.client_list[0])

        # Wait for IO to fill before volume conversion
        sleep(30)

        # Remove arbiter bricks ( arbiter to x2 replicated )
        kwargs = {'replica_count': 2}
        redant.remove_brick(self.server_list[0], self.vol_name,
                            list(self._get_arbiter_bricks()),
                            option='force', replica_count=2)

        # Wait for IO to fill after volume conversion
        sleep(30)

        # Add bricks (x2 replicated to x3 replicated)
        kwargs['replica_count'] = 3
        vol_info = redant.get_volume_info(self.server_list[0], self.vol_name)
        if not vol_info:
            raise Exception('Not able to get volume info')
        dist_count = vol_info[self.vol_name]['distCount']
        _, bricks_cmd = redant.form_brick_cmd(self.server_list,
                                              self.brick_roots, self.vol_name,
                                              mul_fac=int(dist_count),
                                              add_flag=True)
        redant.add_brick(self.vol_name, bricks_cmd, self.server_list[0],
                         force='True', **kwargs)

        # Wait for IO post x3 replicated volume conversion
        sleep(30)

        # Validate volume info
        vol_info = redant.get_volume_info(self.server_list[0], self.vol_name)
        if not vol_info:
            raise Exception('Not able to get volume info')
        repl_count, brick_count = (vol_info[self.vol_name]['replicaCount'],
                                   vol_info[self.vol_name]['brickCount'])

        # Wait for the volfile to sync up on clients
        cmd = (f"grep -ir connected {self.mountpoint}/.meta/graphs/active/"
               f"{self.vol_name}-client-*/private | wc -l")
        wait_time = 300
        in_sync = False
        while wait_time:
            ret = redant.execute_abstract_op_node(cmd, self.client_list[0])
            if int(ret['msg'][0].strip()) == int(brick_count):
                in_sync = True
                break
            sleep(30)
            wait_time -= 30
        if not in_sync:
            raise Exception("Volfiles from clients are not synced even after"
                            " polling for ~5 min")

        if int(repl_count) != kwargs['replica_count']:
            raise Exception("Not able to validate x2 to x3 replicated"
                            " volume conversion")

        # Enable client side heal options, trigger and monitor heal
        options = {
            'data-self-heal': 'on',
            'entry-self-heal': 'on',
            'metadata-self-heal': 'on'
        }
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        if not redant.trigger_heal(self.vol_name, self.server_list[0]):
            raise Exception('Unable to trigger full heal on the volume')

        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # Validate IO
        prev_time = datetime.now().replace(microsecond=0)
        ret = redant.validate_io_procs(self.proc, self.mounts)
        curr_time = datetime.now().replace(microsecond=0)
        if not ret:
            raise Exception('Not able to validate completion of IO on mount')
        self.proc = []

        # To ascertain IO was happening during brick operations
        if curr_time - prev_time <= timedelta(seconds=10):
            raise Exception("Unable to validate IO was happening during brick"
                            " operations")

        # Take and validate `arequal` checksum on first directory
        act_areequal = redant.collect_mounts_arequal(self.mounts, "/user1")
        if exp_arequal != act_areequal:
            raise Exception("`arequal` checksum did not match post arbiter"
                            " to x3 replicated volume conversion")
