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
    Test cases in this module tests directory rmdir with subvol down
"""

# disruptive;dist,dist-rep,dist-disp,dist-arb
from common.ops.gluster_ops.constants import \
    (FILETYPE_DIRS, TEST_LAYOUT_IS_COMPLETE)
from copy import deepcopy
from time import sleep
from tests.d_parent_test import DParentTest


class TestLookupDir(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        if self.volume_type in ("dist-rep", "dist-disp", "dist-arb"):
            conf_hash['dist_count'] = 4

        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def run_test(self, redant):
        """
        case 1: test_rmdir_child_when_nonhash_vol_down
        - create parent
        - bring down a non-hashed subvolume for directory child
        - create parent/child
        - rmdir /mnt/parent will fail with ENOTCONN
        """
        self.subvols = redant.get_subvols(self.vol_name, self.server_list[0])

        # Create parent dir
        parent_dir = f"{self.mountpoint}/parent"
        child_dir = f"{parent_dir}/child"

        redant.create_dir(self.mountpoint, "parent", self.client_list[0])

        # Find a non hashed subvolume(or brick)
        nonhashed_subvol = redant.find_nonhashed_subvol(self.subvols,
                                                        "parent", "child")
        if nonhashed_subvol is None:
            raise Exception("Error in finding nonhashed value")

        count = nonhashed_subvol[1]

        # Bring nonhashed_subbvol offline
        ret = redant.bring_bricks_offline(self.vol_name, self.subvols[count])
        if not ret:
            raise Exception("Error in bringing down subvolume "
                            f"{self.subvols[count]}")

        # Create child-dir
        redant.create_dir(f"{self.mountpoint}/parent", "child",
                          self.client_list[0])

        # 'rmdir' on parent should fail with ENOTCONN
        ret = redant.rmdir(parent_dir, self.client_list[0])
        if ret:
            raise Exception(f'Expected rmdir to fail for {parent_dir}')

        # Cleanup
        # Bring up the subvol - restart volume
        redant.volume_start(self.vol_name, self.server_list[0], force=True)
        sleep(5)

        # Clear mountpoint
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_rmdir_dir_when_hash_nonhash_vol_down
        """
        Steps:
        - create dir1 and dir2
        - bring down hashed subvol for dir1
        - bring down a non-hashed subvol for dir2
        - rmdir dir1 should fail with ENOTCONN
        - rmdir dir2 should fail with ENOTCONN
        """
        # Create dir1 and dir2
        directory_list = []
        for number in range(1, 3):
            directory_list.append(f'{self.mountpoint}/dir{number}')
            cmd = f"mkdir -p {directory_list[-1]}"
            redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Find a non hashed subvolume(or brick)
        nonhashed_subvol = redant.find_nonhashed_subvol(self.subvols, "",
                                                        "dir1")
        if nonhashed_subvol is None:
            raise Exception("Error in finding nonhashed value")
        count = nonhashed_subvol[1]

        # Bring nonhashed_subbvol offline
        ret = redant.bring_bricks_offline(self.vol_name, self.subvols[count])
        if not ret:
            raise Exception("Error in bringing down subvolume "
                            f"{self.subvols[count]}")

        # 'rmdir' on dir1 should fail with ENOTCONN
        ret = redant.rmdir(directory_list[0], self.client_list[0])
        if ret:
            raise Exception(f'Expected rmdir to fail for {directory_list[0]}')

        # Bring up the subvol - restart volume
        redant.volume_start(self.vol_name, self.server_list[0], force=True)
        sleep(5)

        # Unmounting and Mounting the volume back to Heal
        redant.volume_unmount(self.vol_name, self.mountpoint,
                              self.client_list[0])

        redant.volume_mount(self.server_list[0], self.vol_name,
                            self.mountpoint, self.client_list[0])

        redant.execute_abstract_op_node(f"ls {self.mountpoint}/dir1",
                                        self.client_list[0])

        # This confirms that healing is done on dir1
        ret = redant.validate_files_in_dir(self.client_list[0],
                                           directory_list[0],
                                           test_type=TEST_LAYOUT_IS_COMPLETE,
                                           file_type=FILETYPE_DIRS)
        if not ret:
            raise Exception("validate_files_in_dir for dir1 failed")

        # Bring down the hashed subvol
        # Find a hashed subvolume(or brick)
        hashed_subvol = redant.find_hashed_subvol(self.subvols, "", "dir2")
        if hashed_subvol is None:
            raise Exception("Error in finding nonhashed value")
        count = hashed_subvol[1]

        # Bring hashed_subbvol offline
        ret = redant.bring_bricks_offline(self.vol_name, self.subvols[count])
        if not ret:
            raise Exception("Error in bringing down subvolume "
                            f"{self.subvols[count]}")

        # 'rmdir' on dir2 should fail with ENOTCONN
        ret = redant.rmdir(directory_list[1], self.client_list[0])
        if ret:
            raise Exception(f'Expected rmdir to fail for {directory_list[1]}')

        # Cleanup
        # Bring up the subvol - restart the volume
        redant.volume_start(self.vol_name, self.server_list[0], force=True)
        sleep(5)

        # Clear mountpoint
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 3: test_rm_file_when_nonhash_vol_down
        """
        Steps:
        - create parent
        - mkdir parent/child
        - touch parent/child/file
        - bringdown a subvol where file is not present
        - rm -rf parent
            - Only file should be deleted
            - rm -rf of parent should fail with ENOTCONN
        """
        # Find a non hashed subvolume(or brick)
        # Create parent dir
        parent_dir = f"{self.mountpoint}/parent"
        child_dir = f"{parent_dir}/child"

        redant.create_dir(self.mountpoint, "parent", self.client_list[0])

        # Create child dir
        redant.create_dir(f"{self.mountpoint}/parent", "child",
                          self.client_list[0])

        # Create a file under child_dir
        file_one = f"{child_dir}/file_one"
        redant.execute_abstract_op_node(f"touch {file_one}",
                                        self.client_list[0])

        # Find a non hashed subvolume(or brick)
        nonhashed_subvol = redant.find_nonhashed_subvol(self.subvols,
                                                        "parent/child",
                                                        "file_one")
        if nonhashed_subvol is None:
            raise Exception("Error in finding nonhashed value")
        count = nonhashed_subvol[1]

        # Bring nonhashed_subbvol offline
        ret = redant.bring_bricks_offline(self.vol_name, self.subvols[count])
        if not ret:
            raise Exception("Error in bringing down subvolume "
                            f"{self.subvols[count]}")

        # 'rm -rf' on parent should fail with ENOTCONN
        ret = redant.rmdir(parent_dir, self.client_list[0])
        if ret:
            raise Exception(f'Expected rmdir to fail for {parent_dir}')

        bricklist = redant.create_brickpathlist(self.subvols, "parent/child")

        # Make sure file_one is deleted
        for brickdir in bricklist:
            dir_path = f"{brickdir}/parent/child/file_one"
            host, path = dir_path.split(":")
            if redant.path_exists(host, path):
                raise Exception('Expected file to NOT exist on servers')

        # Cleanup
        # Bring up the subvol - restart the volume
        redant.volume_start(self.vol_name, self.server_list[0], force=True)
        sleep(5)

        # Clear mountpoint
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 4: test_rmdir_parent_pre_nonhash_vol_down
        """
        Steps:
        - Bring down a non-hashed subvol for parent_dir
        - mkdir parent
        - rmdir parent should fails with ENOTCONN
        """
        nonhashed_subvol = redant.find_nonhashed_subvol(self.subvols,
                                                        "", "parent")
        if nonhashed_subvol is None:
            raise Exception('Error in finding  nonhashed subvol')
        count = nonhashed_subvol[1]

        # Bring nonhashed_subbvol offline
        ret = redant.bring_bricks_offline(self.vol_name, self.subvols[count])
        if not ret:
            raise Exception("Error in bringing down subvolume "
                            f"{self.subvols[count]}")

        parent_dir = f"{self.mountpoint}/parent"
        redant.create_dir(self.mountpoint, "parent", self.client_list[0])

        # 'rmdir' on parent should fail with ENOTCONN
        ret = redant.rmdir(parent_dir, self.client_list[0])
        if ret:
            raise Exception(f'Expected rmdir to fail for {parent_dir}')
