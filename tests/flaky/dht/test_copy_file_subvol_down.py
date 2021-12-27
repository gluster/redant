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
    TC to check copy of a file when a subvol is down
 *Flaky Test*
 Reason: Client connectivity issue
"""

# disruptive;dist,dist-rep,dist-arb,dist-disp
from copy import deepcopy
from time import sleep
from tests.d_parent_test import DParentTest


class TestCopyFileSubvolDown(DParentTest):

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
        self.redant.execute_abstract_op_node(f"mkdir -p "
                                             f"{self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _create_src_file(self):
        """Create a srcfile"""
        cmd = f"touch {self.mountpoint}/srcfile"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

    def _find_hash_for_src_file(self):
        """Find a new hashsubvol which is different from hash of srcfile"""
        src_hash_subvol = self.redant.find_new_hashed(self.subvols, "",
                                                      "srcfile")
        if not src_hash_subvol:
            raise Exception("Failed to find new hash")

        new_src_name = str(src_hash_subvol[0])
        src_hash_subvol_count = src_hash_subvol[2]
        return new_src_name, src_hash_subvol_count

    def _find_cache_for_src_file(self):
        """Find out hash subvol for srcfile which after rename will become
        cache subvol"""
        src_hashed = self.redant.find_hashed_subvol(self.subvols, "",
                                                    "srcfile")
        if not src_hashed:
            raise Exception("Failed to find hash of subvol")

        src_cache_subvol, src_cache_subvol_count = src_hashed
        return src_cache_subvol_count

    def _rename_src(self, new_src_name):
        """Rename the srcfile to a new name such that it hashes and
        caches to different subvols"""
        ret = self.redant.move_file(self.client_list[0],
                                    f"{self.mountpoint}/srcfile",
                                    f"{self.mountpoint}/{new_src_name}")
        if not ret:
            raise Exception(f"Failed to move file srcfile and {new_src_name}")

    def _create_dest_file_find_hash(self, src_cache_subvol_count,
                                    src_hash_subvol_count):
        """Find a name for dest file such that it hashed to a subvol
           different from the src file's hash and cache subvol"""
        # Get subvol list
        subvol_list = self.redant.get_subvols(self.vol_name,
                                              self.server_list[0])
        if not subvol_list:
            raise Exception("Failed to get subvols")

        for item in (subvol_list[src_hash_subvol_count],
                     subvol_list[src_cache_subvol_count]):
            subvol_list.remove(item)

        # Find name for dest file
        dest_subvol = f"{subvol_list[0][0]}/"
        dest_file = self.redant.find_specific_hashed(self.subvols, "",
                                                     dest_subvol)
        if not dest_file:
            raise Exception("Could not find hashed for destfile")

        # Create dest file
        cmd = f"touch {self.mountpoint}/{dest_file[0]}"
        self.redant.execute_abstract_op_node(cmd, self.client_list[0])

        return dest_file[0], dest_file[2]

    def _kill_subvol(self, subvol_count):
        """Bring down the subvol as the subvol_count"""
        ret = self.redant.bring_bricks_offline(self.vol_name,
                                               self.subvols[subvol_count])
        if not ret:
            raise Exception('Error in bringing down subvolume'
                            f'{self.subvols[subvol_count]}')

    def _copy_src_file_to_dest_file(self, src_file, dest_file,
                                    expected="pass"):
        """
        Copy src file to dest dest, it will either pass or
        fail; as per the scenario
        """
        cmd = f"cd {self.mountpoint}; cp -r {src_file} {dest_file}"
        expected_ret = 0 if expected == "pass" else 1
        ret = self.redant.execute_abstract_op_node(cmd, self.client_list[0],
                                                   False)
        if ret['error_code'] != expected_ret:
            raise Exception("Unexpected: Copy of Src file to dest "
                            f"file status : {expected}")

    def run_test(self, redant):
        """
        Case 1:
        1) Create a volume and start it
        2) Create a src file and a dest file
        3) All subvols are up
        4) Copy src file to dest file
        """
        self.subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not self.subvols:
            raise Exception("Failed to get the volume subvols")

        # Create a src file
        self._create_src_file()

        # Find out cache subvol for src file
        src_cache_count = self._find_cache_for_src_file()

        # Find new hash for src file
        src_file_new, src_hash_count = self._find_hash_for_src_file()

        # Rename src file so it hash and cache to different subvol
        self._rename_src(src_file_new)

        # Create dest file and find its hash subvol
        dest_file, _ = self._create_dest_file_find_hash(src_cache_count,
                                                        src_hash_count)

        # Copy src file to dest file
        self._copy_src_file_to_dest_file(src_file_new, dest_file)

        # Cleanup mount and force start volume for next case
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_copy_srccache_down_srchash_up_desthash_down
        """
        1) Create a volume and start it
        2) Create a src file and a dest file
        3) Bring down the cache subvol for src file
        4) Bring down the hash subvol for dest file
        5) Copy src file to dest file
        """
        # Create a src file
        self._create_src_file()

        # Find out cache subvol for src file
        src_cache_count = self._find_cache_for_src_file()

        # Find new hash for src file
        src_file_new, src_hash_count = self._find_hash_for_src_file()

        # Rename src file so it hash and cache to different subvol
        self._rename_src(src_file_new)

        # Create dest file and find its hash subvol
        dest_file, dest_hash_count = \
            self._create_dest_file_find_hash(src_cache_count, src_hash_count)

        # kill src cache subvol
        self._kill_subvol(src_cache_count)

        # Kill dest hash subvol
        self._kill_subvol(dest_hash_count)

        # Copy src file to dest file
        self._copy_src_file_to_dest_file(src_file_new, dest_file,
                                         expected="fail")

        # Cleanup mount and force start volume for next case
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Add sleep to allow the clients to get back up
        sleep(5)

        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 3: test_copy_srccache_down_srchash_up_desthash_up
        """
        1) Create a volume and start it
        2) Create a src file and a dest file
        3) Bring down the cache subvol for src file
        4) Copy src file to dest file
        """
        # Create a src file
        self._create_src_file()

        # Find out cache subvol for src file
        src_cache_count = self._find_cache_for_src_file()

        # Find new hash for src file
        src_file_new, src_hash_count = self._find_hash_for_src_file()

        # Rename src file so it hash and cache to different subvol
        self._rename_src(src_file_new)

        # Create dest file and find its hash subvol
        dest_file, _ = self._create_dest_file_find_hash(src_cache_count,
                                                        src_hash_count)

        # kill src cache subvol
        self._kill_subvol(src_cache_count)

        # Copy src file to dest file
        self._copy_src_file_to_dest_file(src_file_new, dest_file,
                                         expected="fail")

        # Cleanup mount and force start volume for next case
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Add sleep to allow the clients to get back up
        sleep(5)

        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 4: test_copy_srchash_down_desthash_down
        """
        1) Create a volume and start it
        2) Create a src file and a dest file
        3) Bring down the hash subvol for src file
        4) Bring down the hash subvol for dest file
        5) Copy src file to dest file
        """
        # Create a src file
        self._create_src_file()

        # Find out cache subvol for src file
        src_cache_count = self._find_cache_for_src_file()

        # Find new hash for src file
        src_file_new, src_hash_count = self._find_hash_for_src_file()

        # Rename src file so it hash and cache to different subvol
        self._rename_src(src_file_new)

        # Create dest file and find its hash subvol
        dest_file, dest_hash_count = \
            self._create_dest_file_find_hash(src_cache_count, src_hash_count)

        # Kill the hashed subvol for src file
        self._kill_subvol(src_hash_count)

        # Kill the hashed subvol for dest file
        self._kill_subvol(dest_hash_count)

        # Copy src file to dest file
        self._copy_src_file_to_dest_file(src_file_new, dest_file,
                                         expected="fail")

        # Cleanup mount and force start volume for next case
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Add sleep to allow the clients to get back up
        sleep(5)

        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 5: test_copy_srchash_down_desthash_up
        """
        1) Create a volume and start it
        2) Create a src file and a dest file
        3) Bring down the hash subvol for src file
        4) Copy src file to dest file
        """
        # Create a src file
        self._create_src_file()

        # Find out cache subvol for src file
        src_cache_count = self._find_cache_for_src_file()

        # Find new hash for src file
        src_file_new, src_hash_count = self._find_hash_for_src_file()

        # Rename src file so it hash and cache to different subvol
        self._rename_src(src_file_new)

        # Create dest file and find its hash subvol
        dest_file, _ = self._create_dest_file_find_hash(src_cache_count,
                                                        src_hash_count)

        # Kill the hashed subvol for src file
        self._kill_subvol(src_hash_count)

        # Copy src file to dest file
        self._copy_src_file_to_dest_file(src_file_new, dest_file)

        # Cleanup mount and force start volume for next case
        redant.volume_start(self.vol_name, self.server_list[0], force=True)

        # Add sleep to allow the clients to get back up
        sleep(5)

        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 6: test_copy_srchash_up_desthash_down
        """
        1) Create a volume and start it
        2) Create a src file and a dest file
        3) Bring down the hash subvol for dest file
        4) Copy src file to dest file
        """
        # Create a src file
        self._create_src_file()

        # Find out cache subvol for src file
        src_cache_count = self._find_cache_for_src_file()

        # Find new hash for src file
        src_file_new, src_hash_count = self._find_hash_for_src_file()

        # Rename src file so it hash and cache to different subvol
        self._rename_src(src_file_new)

        # Create dest file and find its hash subvol
        dest_file, dest_hash_count = \
            self._create_dest_file_find_hash(src_cache_count, src_hash_count)

        # Kill the hashed subvol for dest file
        self._kill_subvol(dest_hash_count)

        # Copy src file to dest file
        self._copy_src_file_to_dest_file(src_file_new, dest_file,
                                         expected="fail")
