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
    TC to check truncate while brick is down
"""

# disruptive;disp,dist-disp
# TODO: NFS
from random import sample
from time import sleep
from tests.d_parent_test import DParentTest


class TestEcTruncateFileWithBrickDown(DParentTest):

    def run_test(self, redant):
        """
        Test steps:
        1. Create a volume, start and mount it on a client
        2. Bring down redundant bricks in the subvol
        3. Create a file on the volume using "touch"
        4. Truncate the file using "O_TRUNC"
        5. Bring the brick online
        6. Write data on the file and wait for heal completion
        7. Check for crashes and coredumps
        """
        # pylint: disable=unsubscriptable-object
        for restart_type in ("volume_start", "node_reboot"):
            # Time stamp from mnode for checking cores at the end of test
            ret = redant.execute_abstract_op_node("date +%s",
                                                  self.server_list[0])
            test_timestamp = ret['msg'][0].strip()

            # Create a file using touch
            file_name = f"{self.mountpoint}/test_1"
            redant.execute_abstract_op_node(f"touch {file_name}",
                                            self.client_list[0])

            # List two bricks in each subvol
            subvols = redant.get_subvols(self.vol_name, self.server_list[0])
            if not subvols:
                raise Exception("Failed to get subvols")

            bricks_to_bring_offline = []
            for subvol in subvols:
                bricks_to_bring_offline.extend(sample(subvol, 2))

            # Bring two bricks of each subvol offline
            redant.bring_bricks_offline(self.vol_name,
                                        bricks_to_bring_offline)

            # Validating the bricks are offline or not
            ret = redant.are_bricks_offline(self.vol_name,
                                            bricks_to_bring_offline,
                                            self.server_list[0])
            if not ret:
                raise Exception("Bricks are still online")

            # Truncate the file
            cmd = (f'python -c "import os, sys; fd = os.open({file_name},'
                   ' os.O_TRUNC ); os.close( fd )"')
            redant.execute_abstract_op_node(cmd, self.client_list[0])

            # Bring back the bricks online
            if restart_type == "volume_start":
                # Bring back bricks online by volume start
                redant.volume_start(self.vol_name, self.server_list[0],
                                    force=True)
            else:
                # Bring back the bricks online by node restart
                for brick in bricks_to_bring_offline:
                    node_to_reboot = brick.split(":")[0]
                    redant.reboot_nodes(node_to_reboot)
                    ret = redant.wait_node_power_up(node_to_reboot)
                    if not ret:
                        raise Exception("Failed to reboot node")
                    sleep(60)

            # Check whether bricks are online or not
            ret = redant.are_bricks_online(self.vol_name,
                                           bricks_to_bring_offline,
                                           self.server_list[0])
            if not ret:
                raise Exception(f"Bricks {bricks_to_bring_offline} are still"
                                " offline")

            # write data to the file
            cmd = (f'python -c "import os, sys;fd = os.open({file_name},'
                   ' os.O_RDWR) ;os.write(fd, \'This is test after '
                   'truncate\'.encode()); os.close(fd)"')

            redant.execute_abstract_op_node(cmd, self.client_list[0])

            # Monitor heal completion
            if not redant.monitor_heal_completion(self.server_list[0],
                                                  self.vol_name):
                raise Exception("Heal is not yet completed")

            # check for any crashes on servers and client
            for nodes in (self.server_list, [self.client_list[0]]):
                ret = redant.check_core_file_exists(nodes, test_timestamp)
                if ret:
                    raise Exception(f"Cores found on the {nodes} nodes")
