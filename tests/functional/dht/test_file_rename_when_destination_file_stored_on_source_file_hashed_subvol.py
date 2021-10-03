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
    TC to check file rename when destination file stored on source file
    hashed subvol
"""

# disruptive;dist,dist-rep,dist-disp,dist-arb
import re
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestDhtFileRenameWithDestFileHashed(DParentTest):

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

    @staticmethod
    def _get_remote_subvolume(vol_file_data, brick_name):
        """
        Verifies whether a file is present in given subvol or not
        """
        try:
            brick_name = re.search(r'[a-z0-9\-\_]*', brick_name).group()
            remote_subvol = (vol_file_data[
                brick_name]['option']['remote-subvolume'])
        except KeyError:
            return None
        return remote_subvol

    def _verify_file_links_to_specified_destination(self, host, file_path,
                                                    dest_file):
        """
        Verifies whether a file link points to the specified destination
        """
        ret = self.redant.get_dht_linkto_xattr(host, file_path)
        link_to_xattr = ret[1].split('=')[1][1:-1]

        # Remove unexpected chars in the value, if any
        link_to_xattr = re.search(r'[a-z0-9\-\_]*', link_to_xattr).group()
        if link_to_xattr is None:
            self.redant.logger.error("Failed to get linkto xattr")
            return False

        # Get the remote-subvolume for the corresponding linkto xattr
        path = (f"/var/lib/glusterd/vols/{self.vol_name}/{self.vol_name}."
                "tcp-fuse.vol")
        vol_data = self.redant.parse_vol_file(self.server_list[0], path)
        if not vol_data:
            self.redant.logger.error(f"Failed to parse the file {path}")
            return False

        remote_subvol = self._get_remote_subvolume(vol_data, link_to_xattr)
        if remote_subvol is None:
            # In case, failed to find the remote subvol, get all the
            # subvolumes and then check whether the file is present in
            # any of those sunbol
            subvolumes = vol_data[link_to_xattr]['subvolumes']
            for subvol in subvolumes:
                remote_subvol = self._get_remote_subvolume(vol_data,
                                                           subvol)
                if remote_subvol:
                    subvol = re.search(r'[a-z0-9\-\_]*', subvol).group()
                    remote_host = (
                        vol_data[subvol]['option']['remote-host'])
                    # Verify the new file is in the remote-subvol identified
                    cmd = f"[ -f {remote_subvol}/{dest_file} ]"
                    ret = self.redant.execute_abstract_op_node(cmd,
                                                               remote_host,
                                                               False)
                    if ret['error_code'] == 0:
                        return True
            self.redant.logger.error("The given link file doesn't point "
                                     "to any of the subvolumes")
            return False
        else:
            remote_host = vol_data[link_to_xattr]['option']['remote-host']
            # Verify the new file is in the remote-subvol identified
            cmd = f"[ -f {remote_subvol}/{dest_file} ]"
            ret = self.redant.execute_abstract_op_node(cmd, remote_host,
                                                       False)
            if ret['error_code'] == 0:
                return True
        return False

    def run_test(self, redant):
        """
        Case 1: test_file_rename_when_source_and_dest_hash_diff_subvol
        Steps:
        - Destination file should exist
        - Source file is stored on hashed sub volume(s1) and cached on
          another subvolume(s2)
        - Destination file should be hased to subvolume where source file is
          stored(s2)
        - Destination file should hased subvolume(s2) but cached same
          subvolume(s1) where source file is hashed
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be removed
        - source link file should be removed
        """
        self.subvols = redant.get_subvols(self.vol_name, self.server_list[0])

        # Create soruce file and Get hashed subvol (s2)
        source_hashed_subvol, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file such that the new name hashes to a new subvol (S1)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could'nt find new hashed for destination file")

        # Verify the subvols are not same for source and destination files
        if src_count == new_hashed[2]:
            raise Exception("The subvols for src and dest are same.")

        # Rename/Move the file
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
            raise Exception(f"The New hashed volume {str(new_hashed[0])}"
                            f" doesn't have the expected linkto file")

        # Get a file name that stores to S1 for destination
        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  src_link_subvol,
                                                  new_hashed[0])
        if new_hashed2 is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")

        # Create destination file in subvol S1
        dest_hashed_subvol, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed2[0])))

        # Verify the subvol is S1 itself
        if new_hashed[2] != dest_count:
            raise Exception("The destination file is not stored to desired "
                            f"subvol :{new_hashed[2]}, instead to subvol "
                            f": {dest_count}")

        # Create a linkfile to dest by renaming it to hash to S2
        dest_hashed = redant.find_specific_hashed(self.subvols, "",
                                                  source_hashed_subvol)
        if dest_hashed is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")

        # Verify the subvol is S2
        if dest_hashed[2] != src_count:
            raise Exception("The destination file is not stored to desired "
                            f"subvol: {dest_hashed[2]}, instead to subvol "
                            f": {src_count}")

        # Rename the source file to the new file name
        dest_file_2 = f"{self.mountpoint}/{str(dest_hashed[0])}"
        ret = redant.move_file(self.client_list[0], dest_file, dest_file_2)
        if not ret:
            raise Exception(f"Failed to move files {dest_file} and"
                            f" {dest_file_2}")

        # Verify the Dest link file is stored on sub volume(s2)
        ret = self._verify_link_file_exists(source_hashed_subvol,
                                            str(dest_hashed[0]))
        if not ret:
            raise Exception(f"The hashed subvol {source_hashed_subvol} "
                            "doesn't have the expected linkto file")

        # Rename source to destination
        src = f"{self.mountpoint}/{str(new_hashed[0])}"
        dest_file = f"{self.mountpoint}/{str(dest_hashed[0])}"
        ret = redant.move_file(self.client_list[0], src, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {src} and"
                            f" {dest_file}")

        # Verify destination file is removed
        ret = self._verify_file_exists(dest_hashed_subvol,
                                       str(new_hashed2[0]))
        if ret:
            raise Exception(f"Destination file : {new_hashed2[0]} is not"
                            " removed in subvol")

        # Verify the source link is removed
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception(f"The hashed subvol {src_link_subvol} "
                            "still have the expected linkto file")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_file_rename_when_source_and_dest_hash_same_subvol
        """
        - Destination file should exist
        - Source file is hashed sub volume(s1) and cached on another
          subvolume(s2)
        - Destination file should be hased to same subvolume(s1) where
          source file is hased
        - Destination hashed on subvolume(s1) but should be cached on
          subvolume(s2) where source file is stored
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be there on hashed subvolume and
          should link to new destination file
        - source link file should be removed
        """
        # Create soruce file and Get hashed subvol (s2)
        source_hashed_subvol, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file such that the new name hashes to a new subvol (S1)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could'nt find new hashed for destination file")

        # Verify the subvols are not same for source and destination files
        if src_count == new_hashed[2]:
            raise Exception("The subvols for src and dest are same.")

        # Rename/Move the file
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
            raise Exception(f"The New hashed volume {str(new_hashed[0])}"
                            f" doesn't have the expected linkto file")

        # Get a file name that stores to S2 for destination
        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  source_hashed_subvol)
        if new_hashed2 is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")

        # Create destination file in subvol S2
        dest_hashed_subvol, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed2[0])))

        # Verify the subvol is S2 itself
        if src_count != dest_count:
            raise Exception("The destination file is not stored to desired "
                            f"subvol :{dest_count}")

        # Create a linkfile to dest by renaming it to hash to S1
        dest_hashed = redant.find_specific_hashed(self.subvols, "",
                                                  src_link_subvol,
                                                  new_hashed[0])
        if dest_hashed is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")
        # Verify the subvol is S1
        if dest_hashed[2] != new_hashed[2]:
            raise Exception("The destination file is not stored to desired "
                            f"subvol: {dest_hashed[2]}, instead to subvol:"
                            f" {new_hashed[2]}")

        # Rename the dest file to the new file name
        dest_file_2 = f"{self.mountpoint}/{str(dest_hashed[0])}"
        ret = redant.move_file(self.client_list[0], dest_file, dest_file_2)
        if not ret:
            raise Exception(f"Failed to move files {dest_file} and"
                            f" {dest_file_2}")

        # Rename source to destination
        src = f"{self.mountpoint}/{str(new_hashed[0])}"
        dest_file = f"{self.mountpoint}/{str(dest_hashed[0])}"
        ret = redant.move_file(self.client_list[0], src, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {src} and"
                            f" {dest_file}")

        # Verify destination file is removed
        ret = self._verify_file_exists(dest_hashed_subvol,
                                       str(new_hashed2[0]))
        if ret:
            raise Exception(f"Destination file : {new_hashed2[0]} is not"
                            " removed in subvol")

        # Verify the source link is removed
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception(f"The hashed subvol {src_link_subvol} "
                            "still have the expected linkto file")

        # Verify the Destination link is on hashed subvolume
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(dest_hashed[0]))
        if not ret:
            raise Exception(f"The hashed subvol {dest_hashed_subvol} "
                            "doesn't have the expected linkto file")

        # Verify the dest link file points to new destination file
        host, fqpath = src_link_subvol.split(":")
        file_path = f"{fqpath}{str(dest_hashed[0])}"
        ret = (self._verify_file_links_to_specified_destination(host,
               file_path, str(dest_hashed[0])))
        if not ret:
            raise Exception("The dest link file not pointing towards "
                            "the desired file")

        # Case 3: test_file_rename_when_dest_hash_to_src_subvol
        """
        - Destination file should exist
        - Source file is stored on hashed subvolume it self
        - Destination file should be hased to same subvolume(s1)
          where source file is
        - Destination file hased subvolume(s1) but cached onsubvolume(s2)
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be removed
        """

        # Create soruce file and Get hashed subvol (s1)
        source_hashed_subvol, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a file name that hashes to another subvol (s2)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could'nt find new hashed for destination file")

        # Create destination file in subvol S2
        _, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed[0])))

        # Rename dest file such that it hashes to S1
        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  source_hashed_subvol)
        if new_hashed2 is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")

        # Verify the subvol is S1 itself
        if new_hashed2[2] != src_count:
            raise Exception("The destination file is not stored to desired "
                            "subvol")

        # Rename/Move the file
        dest_file2 = f"{self.mountpoint}/{str(new_hashed2[0])}"
        ret = redant.move_file(self.client_list[0], dest_file, dest_file_2)
        if not ret:
            raise Exception(f"Failed to move files {dest_file} and"
                            f" {dest_file_2}")

        # Verify the Dest link file is stored on hashed sub volume(s1)
        dest_link_subvol = new_hashed2[0]
        ret = self._verify_link_file_exists(dest_link_subvol,
                                            str(new_hashed2[0]))
        if not ret:
            raise Exception(f"The hashed subvol {dest_link_subvol} "
                            "doesn't have the expected linkto file")

        # Rename Source to Dest
        src = f"{self.mountpoint}/test_source_file"
        dest_file = f"{self.mountpoint}/{str(new_hashed2[0])}"
        ret = redant.move_file(self.client_list[0], src, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {src} and"
                            f" {dest_file}")

        # Verify destination file is removed
        ret = self._verify_file_exists(new_hashed[1],
                                       str(new_hashed[0]))
        if ret:
            raise Exception(f"Destination file : {new_hashed[0]} is not"
                            " removed in subvol")

        # Verify the Destination link is removed
        ret = self._verify_link_file_exists(new_hashed2[1],
                                            str(new_hashed2[0]))
        if ret:
            raise Exception(f"The hashed subvol {new_hashed2[1]} still have"
                            " the expected linkto file")

        # Case 4: test_file_rename_when_dest_cache_to_src_subvol
        """
        Steps:
        - Destination file should exist
        - Source file is stored on hashed subvolume it self
        - Destination file should be hased to some other subvolume(s2)
        - Destination file hashed on subvolume(s2) but cached on the
          subvolume(s1) where souce file is present
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be there on hashed subvolume and
          should link to new destination file
        """

        # Create soruce file and Get hashed subvol (s1)
        source_hashed_subvol, src_count, _ = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find name for dest file to cache to S1
        dest_subvol = redant.find_specific_hashed(self.subvols, "",
                                                  source_hashed_subvol)
        if dest_subvol is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")
        dest_name = str(dest_subvol[0])

        # Create destination file in subvol S1
        _, dest_count, _ = self._create_file_and_get_hashed_subvol(dest_name)

        # Verify its subvol (s1)
        if src_count != dest_count:
            raise Exception("The newly created file falls under subvol "
                            f"{dest_count} rather than {src_count}")

        # Rename dest file such that it hashes to some other subvol S2
        dest_hashed_subvol = redant.find_new_hashed(self.subvols, "",
                                                    dest_name)
        if dest_hashed_subvol is None:
            raise Exception("could not find new hashed for dstfile")

        # Rename/Move the file
        dest_file = f"{self.mountpoint}/{dest_hashed_subvol[0]}"
        src_file = f"{self.mountpoint}/{dest_name}"
        ret = redant.move_file(self.client_list[0], src_file, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {src_file} and"
                            f" {dest_file}")

        # Verify the Dest link file is stored on hashed sub volume(s2)
        dest_link_subvol = dest_hashed_subvol[1]
        ret = self._verify_link_file_exists(dest_link_subvol,
                                            str(dest_hashed_subvol[0]))
        if not ret:
            raise Exception(f"The hashed subvol {dest_link_subvol} doesn't"
                            " have the expected linkto file")

        # Rename Source to Dest
        src = f"{self.mountpoint}/test_source_file"
        dest_file = f"{self.mountpoint}/{dest_hashed_subvol[0]}"
        ret = redant.move_file(self.client_list[0], src, dest_file)
        if not ret:
            raise Exception(f"Failed to move files {src} and"
                            f" {dest_file}")

        # Verify destination file is removed
        ret = self._verify_file_exists(dest_subvol[1],
                                       dest_name)
        if ret:
            raise Exception(f"Destination file : {dest_hashed_subvol[0]} is"
                            " not removed in subvol")

        # Verify the Destination link is present
        ret = self._verify_link_file_exists(dest_link_subvol,
                                            str(dest_hashed_subvol[0]))
        if not ret:
            raise Exception(f"The hashed subvol {dest_link_subvol} still "
                            "have the expected linkto file")

        # Verify the dest link file points to new destination file
        host, fqpath = dest_link_subvol.split(":")
        file_path = f"{fqpath}{str(dest_hashed_subvol[0])}"
        ret = (self._verify_file_links_to_specified_destination(host,
               file_path, str(dest_hashed_subvol[0])))
        if not ret:
            raise Exception("The dest link file not pointing towards "
                            "the desired file")
