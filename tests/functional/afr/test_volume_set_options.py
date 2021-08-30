"""
 Copyright (C) 2016-2017  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check volume set options
"""

# disruptive;rep,dist-rep
from time import sleep
from tests.d_parent_test import DParentTest


class TestVolumeSetDataSelfHealTests(DParentTest):

    def run_test(self, redant):
        """
        - turn off self-heal-daemon option
        - turn off data-self-heal option
        - check if the options are set correctly
        - create IO
        - calculate arequal
        If it is distribute-replicate, the  areequal-check sum of nodes
        in each replica set should match
        - bring down "brick1"
        - modify IO
        - bring back the brick1
        - execute "find . | xargs stat" from the mount point
        to trigger background data self-heal
        - calculate arequal
        If it is distribute-replicate, arequal's checksum of brick which
        was down should not match with the bricks which was up
        in the replica set but for other replicaset where all bricks are up
        should match the areequal-checksum
        - check if the data of existing files are not modified in brick1
        - turn on the option data-self-heal
        - execute "find . -type f  | xargs md5sum" from the mount point
        - wait for heal to complete
        - calculate areequal
        If it is distribute-replicate, the  areequal-check sum of nodes
        in each replica set should match
        """
        self.all_mounts_procs = []
        all_bricks = redant.get_all_bricks(self.vol_name, self.server_list[0])

        # Setting options
        options = {"self-heal-daemon": "off",
                   "data-self-heal": "off"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0],
                                  multi_option=True)

        # Check if options are set to off
        options_dict = redant.get_volume_options(self.vol_name,
                                                 node=self.server_list[0])
        if options_dict['cluster.self-heal-daemon'] != "off":
            raise Exception('Option self-heal-daemon is not set to off')
        if options_dict['cluster.data-self-heal'] != "off":
            raise Exception('Option data-self-heal is not set to off')

        # Creating files on client side
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        for mount_obj in self.mounts:
            # Create files
            redant.logger.info('Creating files and dirs...')
            cmd = (f"cd {self.mountpoint}; mkdir test_data_self_heal;"
                   "cd test_data_self_heal; for i in `seq 1 100`; do dd"
                   " if=/dev/urandom of=file.$i bs=128K count=$i ; done;")
            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Check arequals
        # get the subvolumes
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols of volume")
        num_subvols = len(subvols)

        # Get arequals for bricks in each subvol and compare with first brick
        for i in range(0, num_subvols):
            # Get arequal for first brick
            subvol_brick_list = subvols[i]
            arequals = redant.collect_bricks_arequal(subvol_brick_list[0])
            init_val = arequals[0][-1].split(':')[-1]

            # Get arequal for every brick and compare with first brick
            arequals = self.redant.collect_bricks_arequal(subvol_brick_list)
            for brick_arequal in arequals:
                brick_total = brick_arequal[-1].split(':')[-1]
                if init_val != brick_total:
                    raise Exception("Arequals are not equal")

        # Select bricks to bring offline, 1st brick only
        bricks_to_bring_offline = [all_bricks[0]]

        # Get files/dir list
        node, brick_path = bricks_to_bring_offline[0].split(':')
        command = f"cd {brick_path}; ls"
        redant.execute_abstract_op_node(command, node)

        # Get arequal of brick before making offline
        # Get arequals for first subvol and compare
        arequals = redant.collect_bricks_arequal(bricks_to_bring_offline)
        arequal_before_brick_offline = arequals[0][-1].split(':')[-1]

        # Bring brick 1 offline
        redant.bring_bricks_offline(self.vol_name, bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Bricks {bricks_to_bring_offline} are not "
                            "offline")

        # Modify data
        self.all_mounts_procs = []
        for mount_obj in self.mounts:
            # changing files
            command = (f"cd {self.mountpoint}; cd test_data_self_heal; "
                       "for i in `seq 1 100`; do dd if=/dev/urandom "
                       "of=file.$i bs=512K count=$i ; done ;")

            proc = redant.execute_command_async(cmd, mount_obj['client'])
            self.all_mounts_procs.append(proc)

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO validation failed")

        # Bring brick online
        if not redant.bring_bricks_online(self.vol_name, self.server_list,
                                          bricks_to_bring_offline):
            raise Exception("Failed to bring bricks "
                            f"{bricks_to_bring_offline} online")

        # Trigger heal from mount point
        redant.logger.info('Starting heal from mount point...')
        for mount_obj in self.mounts:
            cmd = ("python3 /usr/share/redant/script/file_dir_ops.py stat -R "
                   f"{mount_obj['mountpath']}/test_data_self_heal")
            ret = redant.execute_abstract_op_node(cmd, mount_obj['client'])
            if ret['error_code'] != 0:
                raise Exception(f"Failed to stat on {mount_obj['client']}")

        # Check arequals
        # Get arequals for first subvol and compare
        arequals = redant.collect_bricks_arequal(all_bricks[0])
        first_brick_total = arequals[0][-1].split(':')[-1]

        # Get arequals for all bricks in subvol 0
        for brick in subvols[0]:
            arequals = self.redant.collect_bricks_arequal(brick)
            brick_total = arequals[0][-1].split(':')[-1]

            # Validate that the down brick had different arequal
            if brick != all_bricks[0]:
                if first_brick_total == brick_total:
                    raise Exception("Unexpected: Arequals is same")
            else:
                if first_brick_total != brick_total:
                    raise Exception("Arequals is not same")

        # Get arequals for all subvol except first and compare
        for i in range(1, num_subvols):
            # Get arequal for first brick
            subvol_brick_list = subvols[i]
            arequals = redant.collect_bricks_arequal(subvol_brick_list[0])
            init_val = arequals[0][-1].split(':')[-1]

            # Get arequal for every brick and compare with first brick
            arequals = self.redant.collect_bricks_arequal(subvol_brick_list)
            for brick_arequal in arequals:
                brick_total = brick_arequal[-1].split(':')[-1]
                if init_val != brick_total:
                    raise Exception("Arequals are not equal")

        # Get files/dir list after bringing brick online
        node, brick_path = bricks_to_bring_offline[0].split(':')
        command = f"cd {brick_path}; ls"
        redant.execute_abstract_op_node(command, node)

        # Get arequal of brick after bringing back online
        arequals = redant.collect_bricks_arequal(bricks_to_bring_offline)
        arequal_after_brick_online = arequals[0][-1].split(':')[-1]

        # Compare arequals, it should be same
        if arequal_before_brick_offline != arequal_after_brick_online:
            raise Exception("arequal size on brick before bringing offline "
                            "and ''after bringing online are not equal")

        # Setting options
        time_delay = 5
        options = {"data-self-heal": "on"}
        redant.set_volume_options(self.vol_name, options, self.server_list[0])

        redant.logger.info('Droping client cache')
        command = "echo 3 > /proc/sys/vm/drop_caches"
        redant.execute_abstract_op_node(command, self.client_list[0])

        # Start heal from mount point
        redant.logger.info('Starting heal from mount point...')
        for mount_obj in self.mounts:
            command = (f"cd {self.mountpoint}/test_data_self_heal; "
                       "for i in `ls -1`; do md5sum $i; sleep 1; done;")
            redant.execute_abstract_op_node(command, mount_obj['client'])
            sleep(time_delay)
            command = (f"cd {self.mountpoint}/test_data_self_heal ; "
                       "for i in `ls -1`; do cat $i > /dev/null 2>&1; "
                       "sleep 1; done;")
            redant.execute_abstract_op_node(command, mount_obj['client'])

        # Monitor heal completion
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name):
            raise Exception("Heal is not yet completed")

        # Check if heal is completed
        if not redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Heal is not yet complete")

        # Check for split-brain
        if redant.is_volume_in_split_brain(self.server_list[0],
                                           self.vol_name):
            raise Exception("Volume is in split-brain state")

        # Get arequals and compare
        for i in range(0, num_subvols):
            # Get arequal for first brick
            subvol_brick_list = subvols[i]
            arequals = redant.collect_bricks_arequal(subvol_brick_list[0])
            init_val = arequals[0][-1].split(':')[-1]

            # Get arequal for every brick and compare with first brick
            arequals = self.redant.collect_bricks_arequal(subvol_brick_list)
            for brick_arequal in arequals:
                brick_total = brick_arequal[-1].split(':')[-1]
                if init_val != brick_total:
                    raise Exception("Arequals are not equal")
