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
    TC to check file rename when dest is hashed or cached to diff subvol
    combinations
"""

# disruptive;dist,dist-rep,dist-disp,dist-arb
import re
from copy import deepcopy
from tests.d_parent_test import DParentTest


class TestDhtFileRenameWithDestFile(DParentTest):

    @DParentTest.setup_custom_enable
    def setup_test(self):
        """
        Override the volume create, start and mount in parent_run_test
        """
        conf_hash = deepcopy(self.vol_type_inf[self.volume_type])
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
        ret = self.redant.execute_abstract_op_node(cmd, host, False)
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
        Case 1: test_file_rename_when_dest_doesnt_hash_src_cached_or_hashed
        - Destination file should exist
        - Source file is hashed on sub volume(s1) and cached on
          another subvolume(s2)
        - Destination file should be hased to subvolume(s3) other
          than above two subvolumes
        - Destination file hased on subvolume(s3) but destination file
          should be cached on same subvolume(s2) where source file is stored
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination file hashed on subvolume and should link
          to new destination file
        - source link file should be removed
        """
        self.subvols = redant.get_subvols(self.vol_name, self.server_list[0])

        # Create source file and Get hashed subvol (s2)
        src_subvol, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a new file name for destination file, which hashes
        # to another subvol (s1)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could'nt find new hashed for destination file")

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
            raise Exception(f"The New hashed volume {str(new_hashed[0])}"
                            f" doesn't have the expected linkto file")

        # Identify a file name for dest to get stored in S2
        dest_cached_subvol = redant.find_specific_hashed(self.subvols, "",
                                                         src_subvol)
        if dest_cached_subvol is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")
        # Create the file with identified name
        _, _, dst_file = (self._create_file_and_get_hashed_subvol(
                          str(dest_cached_subvol[0])))

        # Verify its in S2 itself
        if dest_cached_subvol[2] != src_count:
            raise Exception("The subvol found for destination is not same as "
                            "that of the source file cached subvol")

        # Find a subvol (s3) for dest file to linkto, other than S1 and S2
        bricklist = redant.create_brickpathlist(self.subvols, "")
        br_count = -1
        subvol_new = None
        for brickdir in bricklist:
            br_count += 1
            if br_count not in (src_count, new_hashed[2]):
                subvol_new = brickdir
                break

        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  subvol_new)
        if new_hashed2 is None:
            raise Exception("Couldn't find a new hashed subvol "
                            "for destination file")

        # Verify the subvol is not same as S1(src_count) and S2(dest_count)
        if new_hashed2[2] == src_count:
            raise Exception("The subvol found for destination is same as that"
                            " of the source file cached subvol")
        if new_hashed2[2] == new_hashed[2]:
            raise Exception("The subvol found for destination is same as that"
                            " of the source file hashed subvol")

        # Rename the dest file to the new file name
        dst_file_ln = f"{self.mountpoint}/{str(new_hashed2[0])}"
        ret = redant.move_file(self.client_list[0], dst_file, dst_file_ln)
        if not ret:
            raise Exception(f"Failed to move files {dst_file} and"
                            f" {dst_file_ln}")

        # Verify the Dest link file is stored on hashed sub volume(s3)
        dest_link_subvol = new_hashed2[1]
        ret = self._verify_link_file_exists(dest_link_subvol,
                                            str(new_hashed2[0]))
        if not ret:
            raise Exception(f"The hashed subvol {dest_link_subvol} "
                            "doesn't have the expected linkto file")

        # Move/Rename Source File to Dest
        src_file = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], src_file, dst_file)
        if not ret:
            raise Exception(f"Failed to move files {src_file} and"
                            f" {dst_file}")

        # Verify Source file is removed
        ret = self._verify_file_exists(src_subvol, "test_source_file")
        if ret:
            raise Exception("The source file is still present in "
                            f"{src_subvol}")

        # Verify Source link is removed
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception("The source link file is still present in "
                            f"{src_link_subvol}")

        # Verify the Destination link is on hashed subvolume
        ret = self._verify_link_file_exists(dest_link_subvol,
                                            str(new_hashed2[0]))
        if not ret:
            raise Exception(f"The hashed subvol {dest_link_subvol} "
                            "doesn't have the expected linkto file")

        # Verify the dest link file points to new destination file
        host, fqpath = dest_link_subvol.split(":")
        file_path = f"{fqpath}{str(new_hashed2[0])}"
        ret = (self._verify_file_links_to_specified_destination(host,
               file_path, str(dest_cached_subvol[0])))
        if not ret:
            raise Exception("The dest link file not pointing towards "
                            "the desired file")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 2: test_file_rename_when_dest_hash_src_cached
        """
        - Destination file should exist
        - Source file hashed sub volume(s1) and cached on another subvolume(s2)
        - Destination file should be hased to subvolume where source file is
          stored(s2)
        - Destination file hased on subvolume(s2) but should be cached on
          some other subvolume(s3) than this two subvolume
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be removed
        - source link file should be removed
        """
        # Create source file and Get hashed subvol (s2)
        src_subvol, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a new file name for destination file, which hashes
        # to another subvol (s2)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Could'nt find new hashed for destination file")

        # Rename the source file to the new file name
        src_hashed = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], source_file, src_hashed)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {src_hashed}")

        # Verify the Source link file is stored on hashed sub volume(s1)
        src_link_subvol = new_hashed[1]
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if not ret:
            raise Exception(f"The hashed subvol {src_link_subvol} "
                            "doesn't have the expected linkto file")

        # Find a subvol (s3) for dest file to linkto, other than S1 and S2
        bricklist = redant.create_brickpathlist(self.subvols, "")
        br_count = -1
        subvol_new = None
        for brickdir in bricklist:
            br_count += 1
            if br_count not in (src_count, new_hashed[2]):
                subvol_new = brickdir
                break

        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  subvol_new)
        if new_hashed2 is None:
            raise Exception("could not find new hashed for dstfile")

        # Create a file in the subvol S3
        dest_subvol, count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed2[0])))

        # Verify the subvol is not same as S1 and S2
        if count == src_count:
            raise Exception("The subvol found for destination is same as that"
                            " of the source file cached subvol")
        if count == new_hashed[2]:
            raise Exception("The subvol found for destination is same as that"
                            " of the source file hashed subvol")

        # Find a file name that hashes to S2
        dest_hashed = redant.find_specific_hashed(self.subvols, "",
                                                  src_subvol)
        if dest_hashed is None:
            raise Exception("Could not find new hashed for dstfile")

        # Rename destination to hash to S2 and verify
        dest = f"{self.mountpoint}/{str(dest_hashed[0])}"
        ret = redant.move_file(self.client_list[0], dest_file, dest)
        if not ret:
            raise Exception(f"Failed to move files {dest_file} and"
                            f" {dest}")

        # Rename Source File to Dest
        ret = redant.move_file(self.client_list[0], src_hashed, dest)
        if not ret:
            raise Exception(f"Failed to move files {src_hashed} and"
                            f" {dest}")

        # Verify Destination File is removed
        ret = self._verify_file_exists(new_hashed2[1],
                                       str(new_hashed2[0]))
        if ret:
            raise Exception("The Destination file is still present in "
                            f"{dest_subvol}")

        # Verify Source link is removed
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception("The source link file is still present in "
                            f"{src_link_subvol}")

        # Verify Destination Link is removed
        ret = self._verify_link_file_exists(dest_hashed[1],
                                            str(dest_hashed[0]))
        if ret:
            raise Exception("The Dest link file is still present in "
                            f"{dest_hashed[1]}")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 3: test_file_rename_when_src_linked_and_dest_hash_other
        """
        - Destination file should exist
        - Source link file hashed on sub volume(s1) and cached on another
          subvolume(s2)
        - Destination file should be hased to some other
          subvolume(s3)(neither s1 nor s2)
        - Destination file hased on subvolume(s3) but cached on
          subvolume(s1) where source file is hashed
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be there on hashed subvolume
          and should link to new destination file
        - source link file should be removed
        """

        # Create source file and Get hashed subvol (s2)
        _, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a new file name for destination file, which hashes
        # to another subvol (s2)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("couldn't find new hashed for destination file")

        # Rename the source file to the new file name
        src_hashed = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], source_file, src_hashed)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {src_hashed}")

        # Verify the Source link file is stored on hashed sub volume(s1)
        src_link_subvol = new_hashed[1]
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if not ret:
            raise Exception(f"The hashed subvol {src_link_subvol} "
                            "doesn't have the expected linkto file")

        # Find a file name that hashes to S1
        dest_hashed = redant.find_specific_hashed(self.subvols, "",
                                                  new_hashed[1],
                                                  new_hashed[0])
        if dest_hashed is None:
            raise Exception("could not find new hashed for dstfile")

        # Create a file in the subvol S1
        dest_subvol, count, _ = self._create_file_and_get_hashed_subvol(
            str(dest_hashed[0]))

        # Verify the subvol is S1
        if count != new_hashed[2]:
            raise Exception("The subvol found for destination is not same as"
                            " that of the source file hashed subvol")

        # Find a subvol (s3) for dest file to linkto, other than S1 and S2
        bricklist = redant.create_brickpathlist(self.subvols, "")
        br_count = -1
        subvol_new = None
        for brickdir in bricklist:
            br_count += 1
            if br_count not in (src_count, new_hashed[2]):
                subvol_new = brickdir
                break

        new_hashed2 = redant.find_specific_hashed(self.subvols, "",
                                                  subvol_new)
        if new_hashed2 is None:
            raise Exception("could not find new hashed for dstfile")

        # Rename destination to hash to S3 and verify
        dest_src = f"{self.mountpoint}/{str(dest_hashed[0])}"
        dest = f"{self.mountpoint}/{str(new_hashed2[0])}"
        ret = redant.move_file(self.client_list[0], dest_src, dest)
        if not ret:
            raise Exception(f"Failed to move files {dest_src} and"
                            f" {dest}")

        # Rename Source File to Dest
        ret = redant.move_file(self.client_list[0], src_hashed, dest)
        if not ret:
            raise Exception(f"Failed to move files {src_hashed} and"
                            f" {dest}")

        # Verify Destination File is removed
        ret = self._verify_file_exists(dest_hashed[1],
                                       str(dest_hashed[0]))
        if ret:
            raise Exception("The Destination file is still present in "
                            f"{dest_subvol}")

        # Verify Source link is removed
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception("The source link file is still present in "
                            f"{src_link_subvol}")

        # Verify Destination Link is present and points to new dest file
        ret = self._verify_link_file_exists(new_hashed2[1],
                                            str(new_hashed2[0]))
        if not ret:
            raise Exception("The Dest link file is not present in "
                            f"{new_hashed2[1]}")

        host, fqpath = new_hashed2[1].split(":")
        file_path = f"{fqpath}{str(new_hashed2[0])}"
        ret = (self._verify_file_links_to_specified_destination(host,
               file_path, str(new_hashed2[0])))
        if not ret:
            raise Exception("The dest link file not pointing towards "
                            "the desired file")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 4: test_file_rename_when_dest_hash_src_cached_but_hash_other
        """
        - Destination file should exist
        - Source file hashed on sub volume(s1) and cached
          on another subvolume(s2)
        - Destination file should be hased to same subvolume(s1)
          where source file is hashed
        - Destination hased on subvolume(s1) but cached on some other
          subvolume(s3)(neither s1 nor s2)
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be there on hashed subvolume
          and should link to new destination file
        - source link file should be removed
        """

        # Create source file and Get hashed subvol (s2)
        _, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a new file name for destination file, which hashes
        # to another subvol (s2)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Couldn't find new hashed for destination file")

        # Rename the source file to the new file name
        src_hashed = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], source_file, src_hashed)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {src_hashed}")

        # Verify the Source link file is stored on hashed sub volume(s1)
        src_link_subvol = new_hashed[1]
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if not ret:
            raise Exception(f"The hashed subvol {src_link_subvol} "
                            "doesn't have the expected linkto file")

        # Destination file cached on S3.
        # Find a subvol (s3) for dest file to linkto, other than S1 and S2
        bricklist = redant.create_brickpathlist(self.subvols, "")
        br_count = -1
        subvol_new = None
        for brickdir in bricklist:
            br_count += 1
            if br_count not in (src_count, new_hashed[2]):
                subvol_new = brickdir
                break

        dest_cached = redant.find_specific_hashed(self.subvols, "",
                                                  subvol_new)
        if dest_cached is None:
            raise Exception("could not find new hashed for dstfile")

        # Create a file in S3
        _, count, dest_src = self._create_file_and_get_hashed_subvol(
            str(dest_cached[0]))

        # Verify the subvol is not S2 and S1
        if count == new_hashed[2]:
            raise Exception("The subvol found for destination is same as "
                            "that of the source file hashed subvol")
        if count == src_count:
            raise Exception("The subvol found for destination is same as "
                            "that of the source file cached subvol")

        # Rename Destination file such that it hashes to S1
        dest_hashed = redant.find_specific_hashed(self.subvols, "",
                                                  new_hashed[1],
                                                  new_hashed[0])
        if dest_hashed is None:
            raise Exception("Failed to get specific hashed")

        # Verify its S1
        if dest_hashed[2] != new_hashed[2]:
            raise Exception("The subvol found for destination is not same as "
                            "that of the source file hashed subvol")

        # Move dest to new name
        dest = f"{self.mountpoint}/{str(dest_hashed[0])}"
        ret = redant.move_file(self.client_list[0], dest_src, dest)
        if not ret:
            raise Exception(f"Failed to move files {dest_src} and"
                            f" {dest}")

        # Move Source file to Dest
        src = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], src, dest)
        if not ret:
            raise Exception(f"Failed to move files {src} and"
                            f" {dest}")

        # Verify Destination File is removed
        ret = self._verify_file_exists(dest_cached[1],
                                       str(dest_cached[0]))
        if ret:
            raise Exception("The Dest file is still present in "
                            f"{dest_cached[1]}")

        # Verify Source link is removed
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception("The source link file is still present in "
                            f"{src_link_subvol}")

        # Verify Destination Link is present and points to new dest file
        ret = self._verify_link_file_exists(dest_hashed[1],
                                            str(dest_hashed[0]))
        if not ret:
            raise Exception("The Dest link file is not present in "
                            f"{dest_hashed[1]}")

        host, fqpath = dest_hashed[1].split(":")
        file_path = f"{fqpath}{str(dest_hashed[0])}"
        ret = (self._verify_file_links_to_specified_destination(host,
               file_path, str(dest_hashed[0])))
        if not ret:
            raise Exception("The dest link file not pointing towards "
                            "the desired file")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 5: test_file_rename_when_dest_neither_hash_cache_to_src_subvols
        """
        - Destination file should exist
        - Source file hashed on sub volume(s1) and cached on
          another subvolume(s2)
        - Destination file should be hased to some other subvolume(s3)
          (neither s1 nor s2)
        - Destination file hased on subvolume(s3) but cached on
          remaining subvolume(s4)
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be there on hashed subvolume
          and should link to new destination file
        - source link file should be removed
        """
        # Create source file and Get hashed subvol (s2)
        _, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a new file name for destination file, which hashes
        # to another subvol (s2)
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("Couldn't find new hashed for destination file")

        # Rename the source file to the new file name
        src_hashed = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], source_file, src_hashed)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {src_hashed}")

        # Verify the Source link file is stored on hashed sub volume(s1)
        src_link_subvol = new_hashed[1]
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if not ret:
            raise Exception(f"The hashed subvol {src_link_subvol} "
                            "doesn't have the expected linkto file")

        # Destination file cached on S4.
        # Find a subvol (s4) for dest file to linkto, other than S1 and S2
        bricklist = redant.create_brickpathlist(self.subvols, "")
        br_count = -1
        subvol_new = None
        for brickdir in bricklist:
            br_count += 1
            if br_count not in (src_count, new_hashed[2]):
                subvol_new = brickdir
                break

        dest_cached = redant.find_specific_hashed(self.subvols, "",
                                                  subvol_new)
        if dest_cached is None:
            raise Exception("Could not find new hashed for dstfile")

        # Create a file in S3
        _, _, dest_src = self._create_file_and_get_hashed_subvol(
            str(dest_cached[0]))

        # Verify the subvol is not S2 and S1
        if dest_cached[2] == new_hashed[2]:
            raise Exception("The subvol found for destination is same as "
                            "that of the source file hashed subvol")
        if dest_cached[2] == src_count:
            raise Exception("The subvol found for destination is same as "
                            "that of the source file cached subvol")

        # Identify a name for dest that hashes to another subvol S3
        # Find a subvol (s3) for dest file to linkto, other than S1 and S2 and
        # S4
        bricklist = redant.create_brickpathlist(self.subvols, "")
        br_count = -1
        subvol_new = None
        for brickdir in bricklist:
            br_count += 1
            if br_count not in (src_count, new_hashed[2],
                                dest_cached[2]):
                subvol_new = brickdir
                break

        dest_hashed = redant.find_specific_hashed(self.subvols, "",
                                                  subvol_new)
        if dest_hashed is None:
            raise Exception("Could not find specific hashed")

        # Move dest to new name
        dest = f"{self.mountpoint}/{str(dest_hashed[0])}"
        ret = redant.move_file(self.client_list[0], dest_src, dest)
        if not ret:
            raise Exception(f"Failed to move files {dest_src} and"
                            f" {dest}")

        # Move Source file to Dest
        src = f"{self.mountpoint}/{str(new_hashed[0])}"
        ret = redant.move_file(self.client_list[0], src, dest)
        if not ret:
            raise Exception(f"Failed to move files {src} and"
                            f" {dest}")

        # Verify Destination File is removed
        ret = self._verify_file_exists(dest_cached[1],
                                       str(dest_cached[0]))
        if ret:
            raise Exception("The Source file is still present in "
                            f"{dest_cached[1]}")

        # Verify Source link is removed
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed[0]))
        if ret:
            raise Exception("The source link file is still present in "
                            f"{src_link_subvol}")

        # Verify Destination Link is present and points to new dest file
        ret = self._verify_link_file_exists(dest_hashed[1],
                                            str(dest_hashed[0]))
        if not ret:
            raise Exception("The Dest link file is not present in "
                            f"{dest_hashed[1]}")

        host, fqpath = dest_hashed[1].split(":")
        file_path = f"{fqpath}{str(dest_hashed[0])}"
        ret = (self._verify_file_links_to_specified_destination(host,
               file_path, str(dest_hashed[0])))
        if not ret:
            raise Exception("The dest link file not pointing towards "
                            "the desired file")

        # Cleanup
        cmd = f"rm -rf {self.mountpoint}/*"
        redant.execute_abstract_op_node(cmd, self.client_list[0])

        # Case 6: test_file_rename_when_dest_hash_src_hashed_but_cache_diff
        """
        - Destination file should exist
        - Source file is stored on hashed subvolume it self
        - Destination file should be hased to some other subvolume(s2)
        - Destination file hased on subvolume(s2) but cached on some other
          subvolume(s3)(neither s1 nor s2)
            mv <source_file> <destination_file>
        - Destination file is removed.
        - Source file should be renamed as destination file
        - Destination link file should be there on hashed subvolume and
          should link to new destination file
        """

        # Create source file and Get hashed subvol (s1)
        _, src_count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Find a new file name for destination to hash to some subvol S3
        new_hashed = redant.find_new_hashed(self.subvols, "",
                                            "test_source_file")
        if new_hashed is None:
            raise Exception("couldn't find new hashed for destination file")

        # Create Dest file in S3
        dest_cached, dest_count, dest_file = (
            self._create_file_and_get_hashed_subvol(str(new_hashed[0])))

        # Verify S1 and S3 are not same
        if src_count == dest_count:
            raise Exception("The destination file is cached to the source "
                            "cached subvol")

        # Find new name for dest file, that it hashes to some other subvol S2
        bricklist = redant.create_brickpathlist(self.subvols, "")
        br_count = -1
        subvol_new = None
        for brickdir in bricklist:
            br_count += 1
            if br_count not in (src_count, dest_count):
                subvol_new = brickdir
                break

        dest_hashed = redant.find_specific_hashed(self.subvols, "",
                                                  subvol_new)
        if dest_hashed is None:
            raise Exception("Couldn't find specific hashed")

        # Move dest to new name
        dest = f"{self.mountpoint}/{str(dest_hashed[0])}"
        ret = redant.move_file(self.client_list[0], dest_file, dest)
        if not ret:
            raise Exception(f"Failed to move files {dest_file} and"
                            f" {dest}")

        # Move Source file to Dest
        ret = redant.move_file(self.client_list[0], source_file, dest)
        if not ret:
            raise Exception(f"Failed to move files {source_file} and"
                            f" {dest}")

        # Verify Destination File is removed
        ret = self._verify_file_exists(dest_cached,
                                       str(new_hashed[0]))
        if ret:
            raise Exception("The Source file is still present in "
                            f"{dest_cached}")

        # Verify Destination Link is present and points to new dest file
        ret = self._verify_link_file_exists(dest_hashed[1],
                                            str(dest_hashed[0]))
        if not ret:
            raise Exception("The Dest link file is not present in "
                            f"{dest_hashed[1]}")

        host, fqpath = dest_hashed[1].split(":")
        file_path = f"{fqpath}{str(dest_hashed[0])}"
        ret = (self._verify_file_links_to_specified_destination(host,
               file_path, str(dest_hashed[0])))
        if not ret:
            raise Exception("The dest link file not pointing towards "
                            "the desired file")
