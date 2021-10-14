"""
 Copyright (C) 2021 Red Hat, Inc. <http://www.redhat.com>

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
    TC to check self heal with volume expand
"""

# disruptive;dist-rep
import traceback
from random import choice
from tests.d_parent_test import DParentTest


class TestHealWithExpandVolume(DParentTest):

    def terminate(self):
        # Delete non-root users
        try:
            for user in self.users:
                self.redant.del_user(self.client_list[0], user)

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)

        super().terminate()

    def run_test(self, redant):
        """
        Test case:
        1. Created a 2X3 volume.
        2. Mount the volume using FUSE and give 777 permissions to the mount.
        3. Added a new user.
        4. Login as new user and created 100 files from the new user:
           for i in {1..100};do dd if=/dev/urandom of=$i bs=1024 count=1;done
        5. Kill a brick which is part of the volume.
        6. On the mount, login as root user and create 1000 files:
           for i in {1..1000};do dd if=/dev/urandom of=f$i bs=10M count=1;done
        7. On the mount, login as new user, and copy existing data to
           the mount.
        8. Start volume using force.
        9. While heal is in progress, add-brick and start rebalance.
        10. Wait for rebalance and heal to complete,
        11. Check for MSGID: 108008 errors in rebalance logs.
        """
        # Create non-root users
        self.users = ('qa_user', 'qa_admin')
        for user in self.users:
            if not redant.add_user(self.client_list[0], user):
                raise Exception(f"Failed to create non-root user {user}")

        # Change permissions of mount point to 777
        ret = redant.set_file_permissions(self.client_list[0],
                                          self.mountpoint, '-R 777')
        if not ret:
            raise Exception("Unable to change mount point permissions")

        # Create 100 files from non-root user
        cmd = (f"su -l {self.users[0]} -c 'cd {self.mountpoint}; "
               "for i in {1..100};do dd if=/dev/urandom of=nonrootfile$i "
               "bs=1024 count=1; done'")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Kill one brick which is part of the volume
        # Select bricks to bring offline from a replica set
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        self.bricks_to_bring_offline = []
        self.bricks_to_bring_offline.append(choice(subvols[0]))

        # Bring bricks offline
        redant.bring_bricks_offline(self.vol_name,
                                    self.bricks_to_bring_offline)

        if not redant.are_bricks_offline(self.vol_name,
                                         self.bricks_to_bring_offline,
                                         self.server_list[0]):
            raise Exception(f"Bricks {self.bricks_to_bring_offline} are not"
                            " offline")

        # Create 100 files from root user
        cmd = (f"cd {self.mountpoint}; for i in {{1..100}};do dd "
               "if=/dev/urandom of=rootfile$i bs=1M count=1;done")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # On the mount, login as new user, and copy existing data to
        # the mount
        cmd = (f"su -l {self.users[1]} -c 'mkdir new_dir; cd new_dir; "
               "for i in {1..50};do dd if=/dev/urandom of=newuserfile$i "
               f"bs=1024 count=1; done; cd {self.mountpoint}; cp -r ~/ .;'")
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Check if there are files to be healed
        if redant.is_heal_complete(self.server_list[0], self.vol_name):
            raise Exception("Unexpected: Heal is completed")

        # Start the vol using force
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Check if bricks are online
        if not redant.are_bricks_online(self.vol_name,
                                        self.bricks_to_bring_offline,
                                        self.server_list[0]):
            raise Exception(f"Bricks {self.bricks_to_bring_offline} are not"
                            " online even after force start of volume")

        # Add bricks to volume and wait for heal to complete
        ret = redant.expand_volume(self.server_list[0], self.vol_name,
                                   self.server_list, self.brick_roots)
        if not ret:
            raise Exception(f"Failed to add brick to volume {self.volname}")

        # Trigger rebalance and wait for it to complete
        redant.rebalance_start(self.vol_name, self.server_list[0], force=True)

        # Wait for rebalance to complete
        ret = redant.wait_for_rebalance_to_complete(self.vol_name,
                                                    self.server_list[0],
                                                    timeout=6000)
        if not ret:
            raise Exception("Rebalance is not yet complete on the volume")

        # Wait for heal to complete
        if not redant.monitor_heal_completion(self.server_list[0],
                                              self.vol_name,
                                              timeout_period=3600):
            raise Exception("Heal has not yet completed")

        # Check for MSGID: 108008 errors in rebalance logs
        particiapting_nodes = []
        brick_list = redant.get_all_bricks(self.vol_name, self.server_list[0])
        if not brick_list:
            raise Exception("Failed to get the brick list")

        for brick in brick_list:
            node, _ = brick.split(':')
            particiapting_nodes.append(node)

        file = f"/var/log/glusterfs/{self.vol_name}-rebalance.log"
        for server in particiapting_nodes:
            ret = redant.occurences_of_pattern_in_file(server,
                                                       "MSGID: 108008",
                                                       file)
            if ret != 0:
                raise Exception("[Input/output error] present in rebalance "
                                "log file")
