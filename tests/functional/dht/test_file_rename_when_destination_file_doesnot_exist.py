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
"""
# disruptive;dist,dist-rep,dist-disp

from copy import deepcopy
from tests.d_parent_test import DParentTest


class DhtFileRenameVerification(DParentTest):

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
        """ Creates a file and return its hashed subvol
        Args:
               file_name(str): name of the file to be created
        Returns:
                hashed_subvol object: An object of type BrickDir type
                                    representing the hashed subvolume
                subvol_count: The subvol index in the subvol list
                source_file: Path to the file created
        """
        # Create Source File
        source_file = f"{self.mountpoint}/{file_name}"
        self.redant.execute_abstract_op_node(f"touch {source_file}",
                                             self.client_list[0])

        # Find the hashed subvol for source file
        srchashed, scount = self.redant.find_hashed_subvol(self.subvols, "",
                                                           source_file)
        if not srchashed:
            raise Exception("Could not find srchashed")

        return srchashed, scount, source_file

    def _verify_link_file_exists(self, brickdir, file_name):
        """ Verifies whether a file link is present in given subvol
        Args:
               brickdir(Class Object): BrickDir object containing data about
                                       bricks under a specific subvol
        Returns:
                True/False(bool): Based on existance of file link
        """
        brick_node, brick_path = brickdir.split(":")
        file_path = brick_path + file_name
        file_stat = self.redant.get_file_stat(brick_node, file_path)
        if file_stat is None:
            raise Exception(f"Failed to get File stat for {file_path}")
            return False
        if file_stat['msg']['permission'] != 1000:
            raise Exception("Expected file permission to be 1000"
                            f" for {file_path}")
            return False

        # Check for file type to be'sticky empty', have size of 0 and
        # have the glusterfs.dht.linkto xattr set.
        ret = self.redant.is_linkto_file(brick_node, file_path)
        if not ret:
            raise Exception("File is not a linkto file")
            return False
        return True

    def _test_file_rename_when_source_and_dest_hash_diff_subvol(self):
        """
        case 1 :
        - Destination file does not exist
        - Source file is stored on hashed subvolume(s1) it self
        - Destination file should be hashed to some other subvolume(s2)
            mv <source_file> <destination_file>
        - Source file should be renamed to to Destination file.
        - Destination link file should be created on its hashed
          subvolume(s2)
        """
        # Create soruce file and Get hashed subvol (s2)
        _, count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file such that the new name hashes to a new subvol (S1)
        newhash = self.redant.find_new_hashed(self.subvols, "",
                                              "test_source_file")
        if not newhash:
            raise Exception("Could not find new hashed for srcfile")

        dstname = str(newhash[0])
        dstfile = f"{self.mountpoint}/{dstname}"
        dsthashed = newhash[1]
        dcount = newhash[2]

        # Verify the subvols are not same for source and destination files
        if count == dcount:
            raise Exception("The subvols for src and dest are same.")

        # Rename the source file to the destination file
        self.redant.execute_abstract_op_node(f"mv {source_file} {dstfile}",
                                             self.client_list[0])

        # Verify the link file is found in new subvol
        ret = self._verify_link_file_exists(dsthashed, dstname)
        if not ret:
            raise Exception(f"The hashed subvol {dsthashed} doesn't have the "
                            "expected linkto file: {dstname}")

        # cleanup mount for next case
        self.redant.execute_abstract_op_node(f"rm -rf {self.mountpoint}/*",
                                             self.client_list[0])

    def _test_file_rename_when_source_and_dest_hash_same_subvol(self):
        """
        Case 2:
        - Destination file does not exist
        - Source file is stored on hashed subvolume(s1) it self
        - Destination file should be hashed to same subvolume(s1)
            mv <source_file> <destination_file>
        - Source file should be renamed to destination file
        """
        # Create soruce file and Get hashed subvol (s1)
        source_hashed_subvol, count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file such that the new name hashes to a new subvol
        new_hashed = self.redant.find_specific_hashed(self.subvols, "",
                                                      source_hashed_subvol)
        if not new_hashed:
            raise Exception("Could not find hashed for destfile")

        # Rename the source file to the destination file
        dest_file = f"{self.mountpoint}/{new_hashed[2]}"
        self.redant.execute_abstract_op_node(f"mv {source_file} {dest_file}",
                                             self.client_list[0])

        hashed, rcount = self.redant.find_hashed_subvol(self.subvols, "",
                                                        new_hashed[1])
        if not hashed:
            raise Exception("Could not find srchashed")
        if count != rcount:
            raise Exception("The subvols for src and dest are not same.")

        # cleanup mount for next case
        self.redant.execute_abstract_op_node(f"rm -rf {self.mountpoint}/*",
                                             self.client_list[0])

    def _test_file_rename_when_dest_not_hash_to_src_or_src_link_subvol(self):
        """
        Case 3:
        - Destination file does not exist
        - Source link file is stored on hashed sub volume(s1) and Source
          file is stored on another subvolume(s2)
        - Destination file should be hashed to some other subvolume(s3)
          (should not be same subvolumes mentioned in above condition)
             mv <source_file> <destination_file>
        - Source file should be ranamed to destination file
        - source link file should be removed.
        - Destination link file should be created on its hashed
          subvolume(s3)
        """
        # Find a non hashed subvolume(or brick)
        # Create soruce file and Get hashed subvol (s2)
        _, count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file to create link in hashed subvol -(s1)
        newhash = self.redant.find_new_hashed(self.subvols, "",
                                              "test_source_file")
        if not newhash:
            raise Exception("Could not find new hashed for srcfile")

        dstname = str(newhash[0])
        dstfile = f"{self.mountpoint}/{dstname}"
        dsthashed = newhash[1]
        dcount = newhash[2]

        # Rename the source file to the new file name
        self.redant.execute_abstract_op_node(f"mv {source_file} {dstfile}",
                                             self.client_list[0])

        # Verify the Source link file is stored on hashed sub volume(s1)
        ret = self._verify_link_file_exists(dsthashed, dstname)
        if not ret:
            raise Exception(f"The hashed subvol {dsthashed} doesn't have the "
                            "expected linkto file: {dstname}")

        # find a subvol (s3) other than S1 and S2
        brickobject = self.redant.create_brickpathlist(self.subvols, "")
        br_count = -1
        subvol_new = None
        for brickdir in brickobject:
            br_count += 1
            if br_count not in (count, dcount):
                subvol_new = brickdir
                break

        new_hashed2 = self.redant.find_specific_hashed(self.subvols, "",
                                                       subvol_new)
        if not new_hashed2:
            raise Exception("Could not find hashed for destfile")

        # Rename the source file to the destination file
        source_file = f"{self.mountpoint}/{newhash[0]}"
        dest_file = f"{self.mountpoint}/{new_hashed2[2]}"
        self.redant.execute_abstract_op_node(f"mv {source_file} {dest_file}",
                                             self.client_list[0])

        hashed_subvol, rcount = (self.redant.find_hashed_subvol(
                                 self.subvols, "", new_hashed2[1])

        if dcount == rcount:
            raise Exception("The subvols for src and dest are same.")

        # check that the source link file is removed.
        ret = self._verify_link_file_exists(dsthashed, dstname)
        if ret:
            raise Exception(f"The New hashed subvol {dsthashed} still "
                            "have the expected linkto file {dstname}")

        # Check Destination link file is created on its hashed sub-volume(s3)
        ret = self._verify_link_file_exists(hashed_subvol, new_hashed2[1])
        if not ret:
            raise Exception(f"The hashed subvol {hashed_subvol,} doesn't "
                            "have the expected linkto file: {new_hashed2[1]}")

        # cleanup mount for next case
        self.redant.execute_abstract_op_node(f"rm -rf {self.mountpoint}/*",
                                             self.client_list[0])

    def _test_file_rename_when_src_file_and_dest_file_hash_same_subvol(self):
        """
       Case 4:
       - Destination file does not exist
       - Source link file is stored on hashed sub volume(s1) and Source
         file is stored on another subvolume(s2)
       - Destination file should be hashed to same subvolume(s2)
            mv <source_file> <destination_file>
       - Source file should be ranamed to destination file
       - source link file should be removed.
        """
        # Get hashed subvol (S2)
        source_hashed_subvol, count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file to create link in hashed subvol -(s1)
        newhash = self.redant.find_new_hashed(self.subvols, "",
                                              "test_source_file")
        if not newhash:
            raise Exception("Could not find new hashed for srcfile")

        dstname = str(newhash[0])
        dstfile = f"{self.mountpoint}/{dstname}"
        dsthashed = newhash[1]
        dcount = newhash[2]

        # Rename the source file to the new file name
        self.redant.execute_abstract_op_node(f"mv {source_file} {dstfile}",
                                             self.client_list[0])

        # Verify the Source link file is stored on hashed sub volume(s1)
        ret = self._verify_link_file_exists(dsthashed, dstname)
        if not ret:
            raise Exception(f"The hashed subvol {dsthashed} doesn't have the "
                            "expected linkto file: {dstname}")

        # Get a file name to hash to the subvol s2
        new_hashed2 = self.redant.find_specific_hashed(self.subvols, "/",
                                                       source_hashed_subvol)
        if not new_hashed2:
            raise Exception("Could not find hashed for destfile")

        _, rename_count = (self.redant.find_hashed_subvol(
                           self.subvols, "", new_hashed2[1]))

        if count != rename_count:
            raise Exception("The subvols for src and dest are not same.")

        # Move the source file to the new file name
        source_file = f"{self.mountpoint}/{newhash[0]}"
        dest_file = f"{self.mountpoint}/{new_hashed2[2]}"
        self.redant.execute_abstract_op_node(f"mv {source_file} {dest_file}",
                                             self.client_list[0])

        # check that the source link file is removed.
        ret = self._verify_link_file_exists(dsthashed, dstname)
        if ret:
            raise Exception(f"The New hashed subvol {dsthashed} still "
                            "have the expected linkto file {dstname}")

        # cleanup mount for next case
        self.redant.execute_abstract_op_node(f"rm -rf {self.mountpoint}/*",
                                             self.client_list[0])

    def _test_file_rename_when_src_link_and_dest_file_hash_same_subvol(self):
        """
        Case 5:
       - Destination file does not exist
       - Source link file is stored on hashed sub volume(s1) and Source
         file is stored on another subvolume(s2)
       - Destination file should be hashed to same subvolume(s1)
            mv <source_file> <destination_file>
       - Source file should be renamed to destination file
       - Source link file should be removed.
       - Destination link file should be created on its
         hashed subvolume(s1)
        """
        # Get hashed subvol s2)
        _, count, source_file = (
            self._create_file_and_get_hashed_subvol("test_source_file"))

        # Rename the file to create link in another subvol - (s1)
        new_hashed = find_new_hashed(self.subvols, "/", "test_source_file")
        self.assertIsNotNone(new_hashed, ("could not find new hashed subvol "
                                          "for {}".format(source_file)))

        self.assertNotEqual(count,
                            new_hashed.subvol_count,
                            "New file should hash to different sub-volume")

        # Rename the source file to the new file name
        dest_file = "{}/{}".format(self.mount_point, str(new_hashed.newname))
        ret = move_file(self.clients[0], source_file, dest_file)
        self.assertTrue(ret, ("Failed to move file {} and {}"
                              .format(source_file, dest_file)))

        # Verify the Source link file is stored on hashed sub volume(s1)
        src_link_subvol = new_hashed.hashedbrickobject
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed.newname))
        self.assertTrue(ret, ("The New hashed volume {} doesn't have the "
                              "expected linkto file {}"
                              .format(src_link_subvol._fqpath,
                                      str(new_hashed.newname))))

        # Get a file name to hash to the subvol s1
        new_hashed2 = find_specific_hashed(self.subvols,
                                           "/",
                                           src_link_subvol,
                                           new_hashed.newname)
        self.assertIsNotNone(new_hashed2, ("Couldn't find a name hashed to the"
                                           " given subvol {}"
                                           .format(src_link_subvol)))

        _, rename_count = (
            find_hashed_subvol(self.subvols, "/", str(new_hashed2.newname)))
        self.assertEqual(new_hashed.subvol_count, rename_count,
                         "The subvols for src and dest are not same.")

        # Move the source file to the new file name
        source_file = "{}/{}".format(self.mount_point, str(new_hashed.newname))
        dest_file = "{}/{}".format(self.mount_point, str(new_hashed2.newname))
        ret = move_file(self.clients[0], source_file, dest_file)
        self.assertTrue(ret, "Failed to move file")

        # check that the source link file is removed.
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed.newname))
        self.assertFalse(ret, ("The hashed volume {} still have the "
                               "expected linkto file {}"
                               .format(src_link_subvol._fqpath,
                                       str(new_hashed.newname))))
        g.log.info("The source link file is removed")

        # Check Destination link file is created on its hashed sub-volume(s1)
        ret = self._verify_link_file_exists(src_link_subvol,
                                            str(new_hashed2.newname))
        self.assertTrue(ret, ("The New hashed volume {} doesn't have the "
                              "expected linkto file {}"
                              .format(src_link_subvol._fqpath,
                                      str(new_hashed2.newname))))
        g.log.info("Destinaion link is created in desired subvol")

    def run_test(self, redant):
        self.subvols = redant.get_subvols(self.vol_name, self.server_list[0])
        if not self.subvols:
            raise Exception("Failed to get the subvols")

        self._test_file_rename_when_source_and_dest_hash_diff_subvol()
        self._test_file_rename_when_source_and_dest_hash_same_subvol()
        self._test_file_rename_when_dest_not_hash_to_src_or_src_link_subvol()
        self._test_file_rename_when_src_file_and_dest_file_hash_same_subvol()
        self._test_file_rename_when_src_link_and_dest_file_hash_same_subvol()
