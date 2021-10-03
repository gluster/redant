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
    TC to do file rename when destination file exists
"""
# disruptive;dist,dist-rep,dist-disp,dist-arb
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestDhtFileRenameWithDestFile(DParentTest):

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
                                 self.brick_roots, force=True)
        self.mountpoint = (f"/mnt/{self.vol_name}")
        self.redant.execute_abstract_op_node(f"mkdir -p {self.mountpoint}",
                                             self.client_list[0])
        self.redant.volume_mount(self.server_list[0], self.vol_name,
                                 self.mountpoint, self.client_list[0])

    def _create_file_and_get_hashed_subvol(self, file_name):
        """
        Creates a file and return its hashed subvol
        """
        # Create Source File
        source_file = f"{self.mountpoint}/{file_name}"
        self.redant.execute_abstract_op_node(f"touch {source_file}",
                                             self.client_list[0])

        # Find the hashed subvol for source file
        source_hashed = self.redant.find_hashed_subvol(self.subvols, "",
                                                       file_name)
        if source_hashed is None:
            raise Exception("Couldn't find hashed subvol for source file")

        return source_hashed[0], source_hashed[1], source_file

    def _verify_link_file_exists(self, brickdir, file_name):
        """
        Verifies whether a file link is present in given subvol
        """
        host, fqpath = brickdir.split(":")
        file_path = f"{fqpath}{file_name}"
        file_stat = self.redant.get_file_stat(host, file_path)
        if file_stat['error_code'] != 0:
            self.redant.logger.error("Failed to get file stat")
            return False
        if file_stat['msg']['permission'] != 1000:
            self.redant.logger.error(f"Access value not 1000 for {file_path}")
            return False

        # Check for file type to be'sticky empty', have size of 0 and
        # have the glusterfs.dht.linkto xattr set.
        ret = self.redant.is_linkto_file(host, file_path)
        if not ret:
            self.redant.logger.error(f"{file_path} is not a linkto file")
            return False
        return True

    def _verify_file_exists(self, brick_dir, file_name):
        """
        Verifies whether a file is present in given subvol or not
        """
        host, fqpath = brick_dir.split(":")
        cmd = f"[ -f {fqpath}{str(file_name)} ]"
        ret = self.redant.execute_abstract_op_node(cmd, host)
        if ret['error_code'] != 0:
            return False

        return True

    def run_test(self, redant):
        """
        Case 1: test_dht_file_rename_dest_exists_src_and_dest_hash_diff
        Steps:
        - Destination file should exist
        - Source file is stored on hashed subvolume(s1) it self
        - Destination file should be hashed to some other subvolume(s2)
        - Destination file is stored on hashed subvolume
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination hashed file should be created on its hashed
          subvolume(s2)
        """
        self.subvols = redant.get_subvols(self.vol_name, self.server_list[0])

        # Create source file and Get hashed subvol (s1)
        _, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a new file name for destination file, which hashes
        # to another subvol (s2)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could'nt find new hashed for destination file")

        # create destination_file and get its hashed subvol (s2)
        dest_hashed_subvol, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed[0])))

        # Verify the subvols are not same for source and destination files
        if src_count == dest_count:
            raise Exception("The subvols for src and dest are same.")

        # Rename the source file to the destination file
        ret = redant.move_file(self.client_list[0], source_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest_file}")

        # Verify destination file is removed
        ret = self._verify_file_exists(dest_hashed_subvol,
                                       str(new_hashed[0]))
        if not ret:
            raise Exception(f"Destination file : {str(new_hashed[0])} is not"
                            f" removed in subvol: {dest_hashed_subvol}")

        # Verify the Destination link is found in new subvol (s2)
        ret = self._verify_link_file_exists(dest_hashed_subvol,
                                            str(new_hashed[0]))
        if not ret:
            raise Exception(f"The New hashed volume {str(new_hashed[0])}"
                            f" doesn't have the expected linkto file")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_dht_file_rename_dest_exists_src_and_dest_hash_same
        """
        Steps:
        - Destination file should exist
        - Source file is stored on hashed subvolume(s1) it self
        - Destination file should be hashed to same subvolume(s1)
        - Destination file is stored on hashed subvolume
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed to destination file
        """
        # Create soruce file and Get hashed subvol (s1)
        source_hashed_subvol, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a new file name for destination file that hashes
        # to same subvol (s1)
        new_hashed = redant.find_specific_hashed(self.subvols, "",
                                                 source_hashed_subvol)
        if new_hashed is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")

        # Create destination_file and get its hashed subvol (should be s1)
        dest_hashed_subvol, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed[0])))

        # Verify the subvols are same for source and destination files
        if src_count != dest_count:
            raise Exception("The subvols for src and dest are not same.")

        # Rename the source file to the destination file
        ret = redant.move_file(self.client_list[0], source_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest_file}")

        # Verify the file move and the destination file is hashed to
        # same subvol or not
        hashed_subvol = redant.find_hashed_subvol(self.subvols, "",
                                                  str(new_hashed[0]))
        if hashed_subvol is None:
            raise Exception("Failed to get the hashed subvol")
        rename_count = hashed_subvol[1]
        if dest_count != rename_count:
            raise Exception(f"The subvols for source : {source_hashed_subvol}"
                            f" and dest : {dest_hashed_subvol} are not same")

        # Verify destination file is removed
        ret = self._verify_file_exists(dest_hashed_subvol,
                                       str(new_hashed[0]))
        if not ret:
            raise Exception(f"Destination file : {str(new_hashed[0])} is not "
                            "removed")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 3: test_file_rename_dest_exist_and_not_hash_src_srclink_subvol
        """
        Steps:
        - Destination file should exist
        - Source file is hashed sub volume(s1) and
          cached on another subvolume(s2)
        - Destination file should be hashed to some other subvolume(s3)
          (should not be same subvolumes mentioned in above condition)
             mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Souce hashed file should be removed
        - Destination hashed file should be created on its hashed subvolume(s3)
        """
        # Find a non hashed subvolume(or brick)
        # Create soruce file and Get hashed subvol (s2)
        _, count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file to create link in hashed subvol -(s1)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could not find new hashed for dstfile")

        count2 = new_hashed[2]

        # Rename the source file to the new file name
        dest_file = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], source_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest_file}")

        # Verify the Source link file is stored on hashed sub volume(s1)
        src_link_subvol = new_hashed[1]
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if not ret:
            raise Exception(f"The hashed subvol {src_link_subvol} doesn't "
                            "have the expected linkto file")

        # Find a subvol (s3) other than S1 and S2
        bricklist = redant.create_brickpathlist(self.subvols)
        br_count = -1
        subvol_new = None
        for brickdir in bricklist:
            br_count += 1
            if br_count not in (count, count2):
                subvol_new = brickdir
                break

        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  subvol_new)
        if new_hashed2 is None:
            raise Exception("Could not find new hashed for dstfile")

        # Create destination file in a new subvol (s3)
        dest_hashed_subvol, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed2[0])))

        # Verify the subvol is not same as S1 or S2
        if count2 == dest_count:
            raise Exception(f"The subvols for src :{count2} and dest:"
                            f" {dest_count} are same")

        # Verify the subvol is not same as S1 or S2
        if count == dest_count:
            raise Exception(f"The subvols for src :{count} and dest:"
                            f" {dest_count} are same")

        # Rename the source file to the destination file
        source_file = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], source_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest_file}")

        # Verify destination file is removed
        ret = self._verify_file_exists(dest_hashed_subvol,
                                       str(new_hashed2[0]))
        if not ret:
            raise Exception(f"Destination file : {str(new_hashed[0])} is not"
                            " removed in subvol")

        # Check that the source link file is removed.
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception(f"The New hashed volume {src_link_subvol} still"
                            " have the expected linkto file")

        # Check Destination link file is created on its hashed sub-volume(s3)
        ret = self._verify_link_file_exists(dest_hashed_subvol,
                                            str(new_hashed2[0]))
        if not ret:
            raise Exception(f"The New hashed volume {dest_hashed_subvol} "
                            "doesn't have the expected linkto file")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 4: test_file_rename_dest_exist_and_hash_to_src_subvol
        """
        Steps:
        - Destination file should exist
        - Source file is hashed sub volume(s1) and
         cached on another subvolume(s2)
        - Destination file should be hashed to subvolume where source file
         is cached(s2)
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Souce hashed file should be removed
        """
        # Get hashed subvol (S2)
        source_hashed_subvol, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file to create link in hashed subvol -(s1)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could not find new hashed for dstfile")

        # Rename the source file to the new file name
        dest_file = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], source_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest_file}")

        # Verify the Source link file is stored on hashed sub volume(s1)
        src_link_subvol = new_hashed[1]
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if not ret:
            raise Exception(f"The New hashed volume {src_link_subvol} "
                            "doesn't have the expected linkto file")

        # Get a file name for dest file to hash to the subvol s2
        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  source_hashed_subvol)
        if new_hashed2 is None:
            raise Exception("Could not find a name hashed"
                            "to the given subvol")

        # Create destination file in the subvol (s2)
        dest_hashed_subvol, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed2[0])))

        # Verify the subvol is same as S2
        if src_count != dest_count:
            raise Exception("The subvols for src and dest are not same.")

        # Move the source file to the new file name
        source_file = f"{self.mountpoint}/{new_hashed[0]}"
        ret = redant.move_file(self.client_list[0], source_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest_file}")

        # Verify destination file is removed
        ret = self._verify_file_exists(dest_hashed_subvol,
                                       str(new_hashed2[0]))
        if not ret:
            raise Exception(f"Destination file : {new_hashed[0]} is not"
                            f" removed in subvol")

        # Check that the source link file is removed.
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception(f"The New hashed volume {src_link_subvol}"
                            f" still have the expected linkto file")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 5: test_file_rename_dest_exist_and_hash_to_srclink_subvol
        """
        Steps:
        - Destination file should exist
        - Source file is hashed sub volume(s1) and
          cached on another subvolume(s2)
        - Destination file should be hashed to same subvolume(s1) where source
          file is hashed.
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file(cached) should be renamed to destination file
        - Source file(hashed) should be removed.
        - Destination hahshed file should be created on its
          hashed subvolume(s1)
        """
        # Get hashed subvol s2)
        _, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file to create link in another subvol - (s1)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could not find new hashed for dstfile")

        if src_count == new_hashed[2]:
            raise Exception("New file should hash to different sub-volume")

        # Rename the source file to the new file name
        dest_file = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], source_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest_file}")

        # Verify the Source link file is stored on hashed sub volume(s1)
        src_link_subvol = new_hashed[1]
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if not ret:
            raise Exception(f"The New hashed volume {src_link_subvol} "
                            "doesn't have the expected linkto file")

        # Get a file name for dest to hash to the subvol s1
        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  src_link_subvol,
                                                  new_hashed[0])
        if new_hashed2 is None:
            raise Exception("Couldn't find a name hashed to the"
                            f" given subvol {src_link_subvol}")

        # Create destination file in the subvol (s2)
        dest_hashed_subvol, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed2[0])))

        # Verify the subvol is same as S1
        if new_hashed[2] != dest_count:
            raise Exception("The subvols for src and dest are not same.")

        # Move the source file to the new file name
        source_file = f"{self.mountpoint}/{str(new_hashed[0])}"
        dest_file = f"{self.mountpoint}/{str(new_hashed2[0])}"
        ret = redant.move_file(self.client_list[0], source_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest_file}")

        # Verify destination file is removed
        ret = self._verify_file_exists(dest_hashed_subvol,
                                       str(new_hashed2[0]))
        if not ret:
            raise Exception(f"Destination file : {new_hashed[0]} is not "
                            "removed in subvol")

        # Check that the source link file is removed.
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception(f"The hashed volume {src_link_subvol} "
                            "still have the expected linkto file")

        # Check Destination link file is created on its hashed sub-volume(s1)
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed2[0]))
        if not ret:
            raise Exception(f"The New hashed volume {src_link_subvol}"
                            " doesn't have the expected linkto file")
