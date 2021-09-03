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
    Test Cases in this module tests the USS functionality
    before and after snapd is killed. validate snapd after
    volume is started with force option.
"""

# disruptive;rep,dist,dist-rep,disp,dist-disp
from time import sleep
from tests.d_parent_test import DParentTest


class TestSnapshotSnapdCloneVol(DParentTest):

    def _validate_snapd(self, check_condition=True):
        """ Validate snapd running """
        for server in self.brick_servers:
            ret = self.redant.is_snapd_running(self.clone_vol1, server,
                                               excep=False)
            if check_condition:
                if not ret:
                    raise Exception("Unexpected: Snapd is Not running for "
                                    f"volume {self.clone_vol1} on node "
                                    f"{server}")
            else:
                if ret:
                    raise Exception("Unexpected: Snapd is running for "
                                    f"volume {self.clone_vol1} on node "
                                    f"{server}")

    def _validate_uss(self):
        """ Validate USS running """
        ret = self.redant.is_uss_enabled(self.clone_vol1, self.server_list[0])
        if not ret:
            raise Exception("USS is disabled in clone volume "
                            f"{self.clone_vol1}")

    def _validate_snaps(self):
        """ Validate snapshots under .snaps folder """
        self.mounts1 = [{
            "client": self.client_list[0],
            "mountpath": self.mpoint
        }]
        for count in range(0, 40):
            ret = self.redant.view_snaps_from_mount(self.mount1,
                                                    self.snaps_list)
            if ret:
                break
            sleep(2)
            count += 1
        if not ret:
            raise Exception("Failed to lists .snaps folder")

    def run_test(self, redant):
        """
        Steps:
        1. create a volume
        2. Create a snapshots and activate
        3. Clone the snapshot and mount it
        4. Check for snapd daemon
        5. enable uss and validate snapd
        5. stop cloned volume
        6. Validate snapd
        7. start cloned volume
        8. validate snapd
        9. Create 5 more snapshot
        10. Validate total number of
            snapshots created.
        11. Activate 5 snapshots
        12. Enable USS
        13. Validate snapd
        14. kill snapd on all nodes
        15. validate snapd running
        16. force start clone volume
        17. validate snaps inside .snaps directory
        """
        self.mount1 = []
        self.mpoint = "/mnt/clone1"
        self.snap = 'test_snap'
        self.clone_vol1 = 'clone-of-test_snap'

        # Starting I/O
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        all_mounts_procs = []
        for mount_obj in self.mounts:
            proc = redant.create_files('1k', mount_obj['mountpath'],
                                       mount_obj['client'], 10, 'file')
            all_mounts_procs.append(proc)

        # Validate I/O
        if not self.redant.validate_io_procs(all_mounts_procs, self.mounts):
            raise Exception("IO failed on some of the clients")

        # Creating snapshot
        redant.snap_create(self.vol_name, self.snap, self.server_list[0])

        # Activating created snapshots
        redant.snap_activate(self.snap, self.server_list[0])

        # Snapshot list
        ret = redant.get_snap_list(self.server_list[0])
        if len(ret) != 1:
            raise Exception("More than 1 snapshot present even though only 1"
                            " was created")

        # Creating and starting a Clone of snapshot:
        redant.snap_clone(self.snap, self.clone_vol1, self.server_list[0])

        # Start the clone volumes
        redant.volume_start(self.clone_vol1, self.server_list[0])

        # Form server list
        self.brick_servers = []
        brick_list = redant.get_all_bricks(self.clone_vol1,
                                           self.server_list[0])
        if not brick_list:
            raise Exception("Failed to get brick list")
        for bricks in brick_list:
            self.brick_servers.append(bricks.split(":")[0])

        # Get volume info
        volinfo = redant.get_volume_info(self.server_list[0], self.clone_vol1)
        if not volinfo:
            raise Exception("Failed to get vol info")

        # FUSE mount clone1 volume
        cmd = f"mkdir -p  {self.mpoint}"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        redant.volume_mount(self.server_list[0], self.clone_vol1,
                            self.mpoint, self.client_list[0])

        # Validate clone volume is mounted or not
        ret = redant.is_mounted(self.clone_vol1, self.mpoint,
                                self.client_list[0], self.server_list[0])
        if not ret:
            raise Exception("Volume not mounted on mount point: "
                            f"{self.mpoint}")

        # Log Cloned Volume information
        if not (redant.log_volume_info_and_status(self.server_list[0],
                self.clone_vol1)):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.clone_vol1}")

        # Validate snapd running on all nodes
        self._validate_snapd(check_condition=False)

        # Enable USS
        redant.enable_uss(self.clone_vol1, self.server_list[0])

        # Validate USS running
        self._validate_uss()

        # Validate snapd running on all nodes
        self._validate_snapd()

        # Stop cloned volume
        redant.volume_stop(self.clone_vol1, self.server_list[0])

        # Validate snapd running on all nodes
        self._validate_snapd(check_condition=False)

        # Start cloned volume
        redant.volume_start(self.clone_vol1, self.server_list[0])

        # Validate snapd running on all nodes
        self._validate_snapd()

        # Create 5 snapshots
        self.snaps_list = [f"snap{i}" for i in range(0, 5)]
        for snapname in self.snaps_list:
            redant.snap_create(self.clone_vol1, snapname, self.server_list[0])

        # Validate USS running
        self._validate_uss()

        """ Check snapshots under .snaps folder """
        redant.uss_list_snaps(self.client_list[0], self.mpoint)

        # Activate Snapshots
        for snapname in self.snaps_list:
            redant.snap_activate(snapname, self.server_list[0])

        # Validate USS running
        self._validate_uss()

        # Validate snapshots under .snaps folder
        self._validate_snaps()

        # Kill snapd on node and validate snapd except management node
        for server in self.server_list[1:]:
            redant.terminate_snapd_on_node(server)

            # Check snapd running
            if redant.is_snapd_running(self.clone_vol1, server):
                raise Exception("Unexpected: Snapd running on node: "
                                f"{server}")

            # Check snapshots under .snaps folder
            redant.uss_list_snaps(self.client_list[0], self.mpoint)

        # Kill snapd in management node
        redant.terminate_snapd_on_node(self.server_list[0])

        # Validate snapd running on all nodes
        self._validate_snapd(check_condition=False)

        # Validating snapshots under .snaps
        ret = redant.uss_list_snaps(self.client_list[0], self.mpoint,
                                    excep=False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected: Successfully listed "
                            "snapshots under .snaps")

        # Start the Cloned volume(force start)
        redant.volume_start(self.clone_vol1, self.server_list[0], force=True)

        # Validate snapd running on all nodes
        self._validate_snapd()

        # Validate snapshots under .snaps folder
        self._validate_snaps()
