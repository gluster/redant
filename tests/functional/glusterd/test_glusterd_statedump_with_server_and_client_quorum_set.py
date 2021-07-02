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

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 Test Description:
    Check glusterd statedump when server, client quorum is set on volumes.
"""

# disruptive;rep,dist-rep

import traceback
from time import sleep
import socket
from tests.d_parent_test import DParentTest


class TestGlusterdStatedumpWhenQuorumSetOnVolumes(DParentTest):

    def terminate(self):
        # Remove all the statedump files created in the test
        try:
            cmd = "rm -rf /var/run/gluster/glusterdump.*"
            self.redant.execute_abstract_op_node(cmd, self.server_list[0])

        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    def _get_option_value_for_volume(self, option):
        """
        Get value of an option
        """
        option_value = self.redant.get_volume_options('all', option,
                                                      self.server_list[0])
        if not option_value:
            raise Exception(f"Failed to get value of the option {option}")
        return option_value

    def _get_statedump_of_glusterd(self, count):
        """
        Confirm if statedump is collected for glusterd process
        """
        # Get the statedump of glusterd process
        cmd = "kill -USR1 `pidof glusterd`"
        self.redant.execute_abstract_op_node(cmd, self.server_list[0])

        # Added sleep to compensate the creation of the statedump file
        sleep(2)

        # Get the count of statedumps created
        cmd = "ls /var/run/gluster/glusterdump.* | wc -l"
        ret = self.redant.execute_abstract_op_node(cmd, self.server_list[0])
        if int(ret['msg'][0].rstrip('\n')) != count:
            raise Exception("Statedump was not collected under "
                            "/var/run/gluster")

    def _get_value_statedump(self, filename_analyze, value):
        """
        Get value from statedump
        """
        cmd = f"grep '{value}' `{filename_analyze}` | cut -d '=' -f 2"
        ret = self.redant.execute_abstract_op_node(cmd, self.server_list[0])
        return ret['msg']

    def _analyze_statedump(self):
        """
        Analyze the statedump created
        """
        # Select the statedump file to analyze
        file_to_analyze = "ls -t /var/run/gluster/glusterdump.* | head -n 1"

        # Analyze peer hostnames
        hosts_list = self._get_value_statedump(file_to_analyze,
                                               "glusterd.peer*..hostname")
        if len(hosts_list) != (len(self.server_list) - 1):
            raise Exception("Unexpected: All the peers are not present in"
                            " statedump")

        for host in hosts_list:
            found = False
            host_ip = socket.gethostbyname(host.rstrip('\n'))
            if host_ip in self.server_list:
                found = True
            if not found:
                raise Exception(f"Unexpected: Peer {host} not present in"
                                " statedump")

        # Analyze the op-version status
        # Get the max-op-version from statedump
        mx_op_std = self._get_value_statedump(file_to_analyze,
                                              "glusterd.max-op-version")

        # Getting max-op-version
        mx_opvrsn = self._get_option_value_for_volume("cluster.max-op-version")
        if (int(mx_op_std[0].rstrip('\n'))
           != int(mx_opvrsn['cluster.max-op-version'])):
            raise Exception("Unexpected: max-op-version of cluster is not"
                            " equal")

        # Get the current op-version from statedump
        crnt_op_std = self._get_value_statedump(file_to_analyze,
                                                "glusterd.current-op-version")

        # Getting current op-version
        crnt_op_vrsn = self._get_option_value_for_volume("cluster.op-version")
        if (int(crnt_op_std[0].rstrip('\n'))
           != int(crnt_op_vrsn['cluster.op-version'])):
            raise Exception("Unexpected: current op-version of cluster is not"
                            " equal")

        # Check for clients in statedump
        cmd = ("grep 'glusterd.client.*' `%s` | wc -l" % file_to_analyze)
        ret = self.redant.execute_abstract_op_node(cmd, self.server_list[0])
        if int(ret['msg'][0].rstrip('\n')) == 0:
            raise Exception("Unexpected: No client is present in"
                            " statedump")

    def run_test(self, redant):
        """
        Test Case:
        1. Create and start a volume
        2. Fuse mount the volume
        3. Get the glusterd statedump and analyze the statedump
        4. Enable client-side quorum on the volume
        5. Get the glusterd statedump
        6. Delete the volume and peer detach 2 nodes
        7. Create a replica 2 volume and start it
        8. Kill the first brick of the volume
        9. Get the glusterd statedump
        10. Start the volume with force
        11. Enable server-side quorum on the volume
        12. Get the glusterd statedump
        13. Stop glusterd on one of the node
        14. Get the glusterd statedump
        15. Stop glusterd on another node
        16. Get the glusterd statedump
        """
        # pylint: disable=too-many-statements
        if len(self.server_list) < 5:
            self.TEST_RES = None
            raise Exception("Server/Brick requirements not met")

        # Delete old statedumps
        cmd = "rm -rf /var/run/gluster/glusterdump.*"
        redant.execute_abstract_op_node(cmd, self.server_list[0])

        # Get the statedump of glusterd process
        self.dump_count = 1
        self._get_statedump_of_glusterd(self.dump_count)

        # Analyze the statedump created
        self._analyze_statedump()

        # Enable client-side quorum on volume
        option = {"cluster.quorum-type": "auto"}
        redant.set_volume_options(self.vol_name, option, self.server_list[0])

        # Get the statedump of glusterd process
        self.dump_count += 1
        self._get_statedump_of_glusterd(self.dump_count)

        # Delete the volume
        redant.cleanup_volume(self.vol_name, self.server_list[0])

        # Peer detach two nodes
        ret = redant.peer_detach_servers(self.server_list[1:3],
                                         self.server_list[0])
        if not ret:
            raise Exception("Failed to detach the servers")

        # Create and start a new replica 2 volume in the updated cluster
        conf_hash = {
            "dist_count": 1,
            "replica_count": 2,
            "transport": "tcp"
        }
        self.volname = f"{self.test_name}-new-vol"
        redant.setup_volume(self.volname, self.server_list[0],
                            conf_hash, self.server_list[3:],
                            self.brick_roots)

        self.assertTrue(ret, "Failed to create and start the volume: %s"
                        % self.volume_config['name'])

        # Get the list of bricks in volume
        all_bricks = redant.get_all_bricks(self.volname, self.server_list[0])
        if all_bricks is None:
            raise Exception("Failed too get bricks list")

        # Kill the first brick in volume
        ret = redant.bring_bricks_offline(self.volname, all_bricks[0])
        if not ret:
            raise Exception("Failed to bring the bricks down")

        # Get the statedump of glusterd process
        self.dump_count += 1
        self._get_statedump_of_glusterd(self.dump_count)

        # Start the volume with force
        redant.volume_start(self.volname, self.server_list[0], True)

        # Enable server-side quorum on volume
        option = {"cluster.server-quorum-type": "server"}
        self.set_volume_options(self.volname, option, self.server_list[0])

        # Get the statedump of glusterd process
        self.dump_count += 1
        self._get_statedump_of_glusterd(self.dump_count)

        # Stop glusterd process on one of the node.
        redant.stop_glusterd(self.server_list[3])

        # Get the statedump of glusterd process
        self.dump_count += 1
        self._get_statedump_of_glusterd(self.dump_count)

        # Stop glusterd process on one of the node.
        redant.stop_glusterd(self.server_list[4])

        # Get the statedump of glusterd process
        self.dump_count += 1
        self._get_statedump_of_glusterd(self.dump_count)
