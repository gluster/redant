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
    This test verifies remove brick operation on EC
    volume.
"""

# disruptive;dist-disp
import traceback
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestEcRemoveBrickOperations(DParentTest):

    def terminate(self):
        """
        Wait for IO to complete if the TC fails midway
        """
        try:
            if self.is_io_running:
                if not (self.redant.wait_for_io_to_complete(
                        self.all_mounts_procs, self.mounts)):
                    raise Exception("Failed ot wait foer IO to complete")
        except Exception as error:
            tb = traceback.format_exc()
            self.redant.logger.error(error)
            self.redant.logger.error(tb)
        super().terminate()

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        conf_hash['dist_count'] = 4
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

    def run_test(self, redant):
        """
        Steps:
        1. Remove data brick count number of bricks from the volume
           should fail
        2. step 1 with force option should fail
        3. Remove redundant brick count number of bricks from the volume
           should fail
        4. step 3 with force option should fail
        5. Remove data brick count+1 number of bricks from the volume
           should fail
        6. step 5 with force option should fail
        7. Remove disperse count number of bricks from the volume with
           one wrong brick path should fail
        8. step 7 with force option should fail
        9. Start remove brick on first subvol bricks
        10. Remove all the subvols to make a pure EC vol
            by start remove brick on second subvol bricks
        11. Start remove brick on third subvol bricks
        12. Write files and perform read on mountpoints
        """
        self.is_io_running = False
        self.mounts = redant.es.get_mnt_pts_dict_in_list(self.vol_name)
        self.all_mounts_procs, count = [], 1

        # Start IOs on mountpoint
        for mount_obj in self.mounts:
            proc = redant.create_deep_dirs_with_files(mount_obj['mountpath'],
                                                      count, 2, 5, 3, 3,
                                                      mount_obj['client'])
            self.all_mounts_procs.append(proc)
            count += 10
        self.is_io_running = True

        # Get subvols
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get the subvols")

        volinfo = redant.get_volume_info(self.server_list[0], self.vol_name)
        initial_brickcount = volinfo[self.vol_name]['brickCount']
        data_brick_count = (volinfo[self.vol_name]['disperseCount']
                            - volinfo[self.vol_name]['redundancyCount'])

        # Try to remove data brick count number of bricks from the volume
        bricks_list_to_remove = (subvols[0][0:data_brick_count])
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  bricks_list_to_remove, option='start',
                                  excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"ERROR: Removed bricks {bricks_list_to_remove}"
                            f" from the volume {self.vol_name}")

        # Trying with force option
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  bricks_list_to_remove, option='force',
                                  excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"ERROR: Removed bricks {bricks_list_to_remove}"
                            f" from the volume {self.vol_name}")

        # Try to remove redundant brick count number of bricks from the volume
        bricks_list_to_remove = (subvols[0][0:volinfo[self.vol_name]
                                            ['redundancyCount']])
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  bricks_list_to_remove, option='start',
                                  excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"ERROR: Removed bricks {bricks_list_to_remove}"
                            f" from the volume {self.vol_name}")

        # Trying with force option
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  bricks_list_to_remove, option='force',
                                  excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"ERROR: Removed bricks {bricks_list_to_remove}"
                            f" from the volume {self.vol_name}")

        # Try to remove data brick count+1 number of bricks from the volume
        bricks_list_to_remove = (subvols[0][0:data_brick_count + 1])
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  bricks_list_to_remove, option='start',
                                  excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"ERROR: Removed bricks {bricks_list_to_remove}"
                            f" from the volume {self.vol_name}")

        # Trying with force option
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  bricks_list_to_remove, option='force',
                                  excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"ERROR: Removed bricks {bricks_list_to_remove}"
                            f" from the volume {self.vol_name}")

        # Try to remove disperse count number of bricks from the volume with
        # one wrong brick path
        bricks_list_to_remove = (subvols[0][0:volinfo[self.vol_name]
                                            ['disperseCount']])
        bricks_list_to_remove[0] = f"{bricks_list_to_remove[0]}-wrong_path"
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  bricks_list_to_remove, option='start',
                                  excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"ERROR: Removed bricks {bricks_list_to_remove}"
                            f" from the volume {self.vol_name}")

        # Trying with force option
        ret = redant.remove_brick(self.server_list[0], self.vol_name,
                                  bricks_list_to_remove, option='force',
                                  excep=False)
        if ret['msg']['opRet'] == '0':
            raise Exception(f"ERROR: Removed bricks {bricks_list_to_remove}"
                            f" from the volume {self.vol_name}")

        # Verify that the brick count is intact
        volinfo = redant.get_volume_info(self.server_list[0], self.vol_name)
        latest_brickcount = volinfo[self.vol_name]['brickCount']
        if latest_brickcount != initial_brickcount:
            raise Exception("Brick count is not expected to "
                            "change, but changed")

        # Start remove brick on first subvol bricks
        bricks_list_to_remove = subvols[0]
        redant.remove_brick(self.server_list[0], self.vol_name,
                            bricks_list_to_remove, option='start')

        # Verify that the brick count is intact
        volinfo = redant.get_volume_info(self.server_list[0], self.vol_name)
        latest_brickcount = volinfo[self.vol_name]['brickCount']
        if latest_brickcount != initial_brickcount:
            raise Exception("Brick count is not expected to "
                            "change, but changed")

        # Wait for remove brick to complete
        ret = redant.wait_for_remove_brick_to_complete(self.server_list[0],
                                                       self.vol_name,
                                                       bricks_list_to_remove)
        if not ret:
            raise Exception("Remove brick is not yet complete on the volume "
                            f"{self.vol_name}")

        # Commit the remove brick operation
        redant.remove_brick(self.server_list[0], self.vol_name,
                            bricks_list_to_remove, option='commit')

        # Remove all the subvols to make a pure EC vol
        # Start remove brick on second subvol bricks
        bricks_list_to_remove = subvols[1]
        redant.remove_brick(self.server_list[0], self.vol_name,
                            bricks_list_to_remove, option='start')

        # Wait for remove brick to complete
        ret = redant.wait_for_remove_brick_to_complete(self.server_list[0],
                                                       self.vol_name,
                                                       bricks_list_to_remove)
        if not ret:
            raise Exception("Remove brick is not yet complete on the volume "
                            f"{self.vol_name}")

        # Commit the remove brick operation
        redant.remove_brick(self.server_list[0], self.vol_name,
                            bricks_list_to_remove, option='commit')

        # Start remove brick on third subvol bricks
        bricks_list_to_remove = subvols[2]
        redant.remove_brick(self.server_list[0], self.vol_name,
                            bricks_list_to_remove, option='start')

        # Wait for remove brick to complete
        ret = redant.wait_for_remove_brick_to_complete(self.server_list[0],
                                                       self.vol_name,
                                                       bricks_list_to_remove)
        if not ret:
            raise Exception("Remove brick is not yet complete on the volume "
                            f"{self.vol_name}")

        # Commit the remove brick operation
        redant.remove_brick(self.server_list[0], self.vol_name,
                            bricks_list_to_remove, option='commit')

        # Log volume info and status
        if not redant.log_volume_info_and_status(self.server_list[0],
                                                 self.vol_name):
            raise Exception("Logging volume info and status failed "
                            f"on volume {self.volname}")

        # Validate IO
        ret = redant.validate_io_procs(self.all_mounts_procs, self.mounts)
        if not ret:
            raise Exception("IO failed on some of the clients")
        self.is_io_running = False

        # Write some files on the mount point
        cmd1 = (f"cd {self.mountpoint}; mkdir test; cd test; "
                "for i in `seq 1 100` ;do touch file$i; done")
        redant.execute_abstract_op_node(cmd1, self.client_list[0])

        # Perform read operation on mountpoint
        cmd2 = f"cd {self.mountpoint}; ls -lRt;"
        redant.execute_abstract_op_node(cmd2, self.client_list[0])
