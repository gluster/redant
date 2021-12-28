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
    TC to check copy of a dir when a subvol is down
 *Flaky Test*
 Reason: Client connectivity issue
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
from copy import deepcopy
from time import sleep
from tests.d_parent_test import DParentTest


class TestCopyDirSubvolDown(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
        if self.volume_type == "dist":
            conf_hash['dist_count'] = 4
        else:
            conf_hash['dist_count'] = 3
        self.redant.setup_volume(self.vol_name, self.server_list[0],
                                 conf_hash, self.server_list,
                                 self.brick_roots)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _create_src(self, m_point):
        """
        Create the source directory and files under the
        source directory.
        """
        # Create source dir
        self.redant.create_dir(m_point, "src_dir", self.client_list[0])

        # Create files inside source dir
        proc = self.redant.create_files("1k", f"{m_point}/src_dir/",
                                        self.client_list[0], 100)
        mounts = {
            "client": self.client_list[0],
            "mountpath": self.mountpoint
        }
        if not self.redant.validate_io_procs(proc, mounts):
            raise Exception("IO failed on the client")

    def _copy_files_check_contents(self, m_point, dest_dir):
        """
        Copy files from source directory to destination
        directory when it hashes to up-subvol and check
        if all the files are copied properly.
        """
        mounts = {
            "client": self.client_list[0],
            "mountpath": m_point
        }
        # collect arequal checksum on src dir
        src_checksum = self.redant.collect_mounts_arequal(mounts, "src_dir")

        # copy src_dir to dest_dir
        cmd = f"cd {m_point}; cp -r src_dir {dest_dir}"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        # collect arequal checksum on destination dir
        dest_checksum = self.redant.collect_mounts_arequal(mounts, dest_dir)

        # Check if the contents of src dir are copied to
        # dest dir
        if src_checksum != dest_checksum:
            raise Exception('All the contents of src dir are not'
                            ' copied to dest dir')

    def _copy_when_dest_hash_down(self, m_point, dest_dir):
        """
        Copy files from source directory to destination
        directory when it hashes to down-subvol.
        """
        # copy src_dir to dest_dir (should fail as hash subvol for dest
        # dir is down)
        cmd = f"cd {m_point}; cp -r src_dir {dest_dir}"
        ret = self.redant.execute_abstract_op_node(cmd, self.client_list[0],
                                                   False)
        if ret['error_code'] == 0:
            raise Exception("Unexpected : Copy of src dir to"
                            " dest dir passed")

    def run_test(self, redant):
        """
        Case 1:
        - Create directory from mount point.
        - Copy dir ---> Bring down dht sub-volume where destination
          directory hashes to down sub-volume.
        - Copy directory and make sure destination dir does not exist
        """
        # Create source dir
        redant.create_dir(self.mountpoint, "src_dir", self.client_list[0])

        # Get subvol list
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")

        # Find out the destination dir name such that it hashes to
        # different subvol
        newdir = redant.find_new_hashed(subvols, "", "src_dir")
        if not newdir:
            raise Exception("Failed to get new hashed subvol")
        dest_dir = str(newdir[0])
        dest_count = newdir[2]

        # Kill the brick/subvol to which the destination dir hashes
        ret = redant.bring_bricks_offline(self.vol_name, subvols[dest_count])
        if not ret:
            raise Exception("Error in bringing down subvolume "
                            f"{subvols[dest_count]}")

        # Copy src_dir to dest_dir (should fail as hash subvol for dest
        # dir is down)
        self._copy_when_dest_hash_down(self.mountpoint, dest_dir)

        # Cleanup mount and force start volume for next case
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Add sleep to allow the clients to get back up
        sleep(5)

        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_copy_existing_dir_dest_subvol_up
        """
        - Create files and directories from mount point.
        - Copy dir ---> Bring down dht sub-volume where destination
          directory should not hash to down sub-volume
        - copy dir and make sure destination dir does not exist
        """
        # Create source dir and create files inside it
        self._create_src(self.mountpoint)

        # Get subvol list
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")

        # Find out hashed brick/subvol for src dir
        src_hashed = redant.find_hashed_subvol(subvols, "", "src_dir")
        if not src_hashed:
            raise Exception("Could not find srchashed")
        src_subvol, src_count = src_hashed

        # Find out the destination dir name such that it hashes to
        # different subvol
        newdir = redant.find_new_hashed(subvols, "", "src_dir")
        if not newdir:
            raise Exception("Failed to get new hashed subvol")
        dest_dir = str(newdir[0])
        dest_count = newdir[2]

        # Remove the hashed subvol for dest and src dir from the
        # subvol list
        for item in (subvols[src_count], subvols[dest_count]):
            subvols.remove(item)

        # Bring down a DHT subvol
        ret = redant.bring_bricks_offline(self.vol_name, subvols[0])
        if not ret:
            raise Exception(f"Error in bringing down subvolume {subvols[0]}")

        # Create files on source dir and
        # perform copy of src_dir to dest_dir
        self._copy_files_check_contents(self.mountpoint, dest_dir)

        # Cleanup mount and force start volume for next case
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Add sleep to allow the clients to get back up
        sleep(5)

        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 3: test_copy_new_dir_dest_subvol_up
        """
        - Copy dir ---> Bring down dht sub-volume where destination
          directory should not hash to down sub-volume
        - Create files and directories from mount point.
        - copy dir and make sure destination dir does not exist
        """
        # Get subvols
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")

        # Find out hashed brick/subvol for src dir
        src_hashed = redant.find_hashed_subvol(subvols, "", "src_dir")
        if not src_hashed:
            raise Exception("Could not find srchashed")
        src_subvol, src_count = src_hashed

        # Find out the destination dir name such that it hashes to
        # different subvol
        newdir = redant.find_new_hashed(subvols, "", "src_dir")
        if not newdir:
            raise Exception("Failed to get new hashed subvol")
        dest_dir = str(newdir[0])
        dest_count = newdir[2]

        # Remove the hashed subvol for dest and src dir from the
        # subvol list
        for item in (subvols[src_count], subvols[dest_count]):
            subvols.remove(item)

        # Bring down a dht subvol
        ret = redant.bring_bricks_offline(self.vol_name, subvols[0])
        if not ret:
            raise Exception(f"Error in bringing down subvolume {subvols[0]}")

        # Create source dir and create files inside it
        self._create_src(self.mountpoint)

        # Create files on source dir and
        # perform copy of src_dir to dest_dir
        self._copy_files_check_contents(self.mountpoint, dest_dir)

        # Cleanup mount and force start volume for next case
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Add sleep to allow the clients to get back up
        sleep(8)

        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 4: test_copy_new_dir_dest_subvol_down
        """
        - Copy dir ---> Bring down dht sub-volume where destination
          directory hashes to down sub-volume
        - Create directory from mount point.
        - Copy dir and make sure destination dir does not exist
        """
        # Get subvol list
        subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not subvols:
            raise Exception("Failed to get subvols")

        # Find out the destination dir name such that it hashes to
        # different subvol
        newdir = redant.find_new_hashed(subvols, "", "src_dir")
        if not newdir:
            raise Exception("Failed to get new hashed subvol")
        dest_dir = str(newdir[0])
        dest_count = newdir[2]

        # Bring down the hashed-subvol for dest dir
        ret = redant.bring_bricks_offline(self.vol_name, subvols[dest_count])
        if not ret:
            raise Exception("Error in bringing down subvolume "
                            f"{subvols[dest_count]}")

        # Create source dir
        redant.create_dir(self.mountpoint, "src_dir", self.client_list[0])

        # Copy src_dir to dest_dir (should fail as hash subvol for dest
        # dir is down)
        self._copy_when_dest_hash_down(self.mountpoint, dest_dir)
