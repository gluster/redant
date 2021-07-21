"""
 Copyright (C) 2017-2020  Red Hat, Inc. <http://www.redhat.com>

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
    TC to check snap info when a peer is detached
"""

# disruptive;
import random
from tests.d_parent_test import DParentTest


class TestSnapInfoOnPeerDetachedNode(DParentTest):

    def run_test(self, redant):
        """
        Create a volume with single brick
        Create a snapshot
        Activate the snapshot created
        Enabled uss on the volume
        Validated snap info on all the nodes
        Peer detach one node
        Validate /var/lib/glusterd/snaps on the detached node
        Probe the detached node
        """

        # Creating volume with single brick on one node
        brick_dict, bricks_cmd = redant.form_brick_cmd(self.server_list[0],
                                                       self.brick_roots,
                                                       self.vol_name, 1)
        conf_hash = {
            "dist_count": 1,
            "replica_count": 1,
            "transport": "tcp"
        }
        redant.volume_create_with_custom_bricks(self.vol_name,
                                                self.server_list[0],
                                                conf_hash, bricks_cmd,
                                                brick_dict)

        # Create a snapshot of the volume without volume start should fail
        self.snapname = "snap1"
        ret = redant.snap_create(self.vol_name, self.snapname,
                                 self.server_list[0], excep=False)
        if ret['msg']['opRet'] == 0:
            raise Exception("Unexpected: Snapshot creation succeeded without"
                            " starting the volume")

        # Start the volume
        redant.volume_start(self.vol_name, self.server_list[0])

        # Create a snapshot of the volume after volume start
        redant.snap_create(self.vol_name, self.snapname,
                           self.server_list[0], excep=False)

        # Activate snapshot created
        redant.snap_activate(self.snapname, self.server_list[0])

        # Enable uss
        option = {'features.uss': 'enable'}
        redant.set_volume_options(self.vol_name, option, self.server_list[0])

        # Validate files /var/lib/glusterd/snaps on all the servers is same
        pathname = f"/var/lib/glusterd/snaps/{self.snapname}"
        for server in self.server_list:
            ret = redant.path_exists(server, pathname)
            if not ret:
                raise Exception(f"Path {pathname} doesn't exist on {server}")

        # Peer detach one node
        random_node = random.choice(self.server_list[1:])
        if not redant.peer_detach_servers(random_node, self.server_list[0]):
            raise Exception(f"Failed to detach the peer {random_node}")

        # /var/lib/glusterd/snaps/<snapname> directory should not present
        ret = redant.path_exists(random_node, pathname)
        if ret:
            raise Exception(f"Unexpected: Path {pathname} exists on "
                            f"{random_node}")
