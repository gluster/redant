"""
DHT ops contain methods which deals with DHT operations like
hashing, layout and so on.
"""

import ctypes
from common.ops.abstract_ops import AbstractOps


class DHTOps(AbstractOps):
    """
    Class which is responsible for methods DHT operations
    """
    def check_hashrange(self, brickdir_path: str) -> list:
        """Check the hash range for a brick

        Args:
            brickdir_path (str): path of the directory as returned from
                                 pathinfo
            (e.g., server1.example.com:/bricks/brick1/testdir1)

        Returns:
            list containing the low and high hash for the brickdir.
            None on fail.
        """
        host, fqpath = brickdir_path.split(':')
        command = (f"getfattr -n trusted.glusterfs.dht -e hex {fqpath} "
                   "2> /dev/null | grep -i trusted.glusterfs.dht | "
                   "cut -d= -f2")
        ret = self.execute_abstract_op_node(command, host, False)
        if ret['error_code'] != 0:
            self.logger.error("Failed to get the hash range for the brick."
                              f"Error: {ret['error_msg']}")
            return None

        full_hash_hex = ret['msg'][0].strip()
        # Grab the trailing 16 hex bytes
        trailing_hash_hex = full_hash_hex[-16:]
        # Split the full hash into low and high
        hash_range_low = int(trailing_hash_hex[0:8], 16)
        hash_range_high = int(trailing_hash_hex[-8:], 16)

        return [hash_range_low, hash_range_high]

    def get_hashrange(self, brickdir_path: str) -> list:
        """
        Get the int hash range for a brick.

        Note:
            If the Gluster version is equal to or greater than 6, the hash
            range can be calculated only for distributed,
            distributed-dispersed, distributed-arbiter and
            distributed-replicated volume types because of DHT pass-through
            option which was introduced in Gluster 6.

            About DHT pass-through option:
            There are no user controllable changes with this feature.
            The distribute xlator now skips unnecessary checks and operations
            when the distribute count is one for a volume, resulting in
            improved performance.It comes into play when there is only 1 brick
            or it is a pure-replicate or pure-disperse or pure-arbiter volume.

        Args:
            brickdir_path (str): path of the directory as returned from
                                 pathinfo
            (e.g., server1.example.com:/bricks/brick1/testdir1)

        Returns:
            list containing the low and high hash for the brickdir.
            None on fail.
        """
        host, _ = brickdir_path.split(':')
        ver = self.get_gluster_version(host)
        ret = self.get_volume_type_from_brickpath(brickdir_path)
        if ret in ('Replicate', 'Disperse', 'Arbiter') and float(ver) >= 6.0:
            self.logger.info("Cannot find hash-range for Replicate/Disperse/"
                             "Arbiter volume type")
            return None
        else:
            ret = self.check_hashrange(brickdir_path)
            if ret is None:
                self.logger.error("Could not get hashrange")
                return None

            hash_range_low = ret[0]
            hash_range_high = ret[1]
            return [hash_range_low, hash_range_high]

    def hashrange_contains_hash(self, brickdir_path: str,
                                filehash: int) -> bool:
        """
        Check if a hash number falls between the brick hashrange

        Args:
            brickdir_path (str): Brickpath for which hashrange is to be
                                 checked
            filehash (int): hash being checked against range

        Returns:
            True if hash is in range. False if hash is out of range
        """
        hashrange = self.get_hashrange(brickdir_path)
        if hashrange is None:
            return False

        if hashrange[0] <= filehash <= hashrange[1]:
            return True

        return False

    def is_layout_complete(self, node: str, volname: str,
                           dirpath: str) -> bool:
        """
        This function reads the subvols in the given volume and checks
        whetherlayout is complete or not.
        Layout starts at zero,
        ends at 32-bits high,
        and has no holes or overlaps

        Args:
            node (str): Node on which command has to be executed
            volname (str): volume name
            dirpath (str): directory path; starting from root of mount point.

        Returns (bool): True if layout is complete
                        False if layout has any holes or overlaps

        Example:
            is_layout_complete("abc.xyz.com", "testvol", "/")
            is_layout_complete("abc.xyz.com", "testvol", "/dir1/dir2/dir3")
        """
        # Get subvols for the volume
        subvols_list = self.get_subvols(volname, node)
        trim_subvols_list = [y for x in subvols_list for y in x]

        # append the dirpath to the elements in the list
        final_subvols_list = [x + dirpath for x in trim_subvols_list]

        complete_hash_list = []
        for fqpath in final_subvols_list:
            hash_list = self.get_hashrange(fqpath)
            complete_hash_list.append(hash_list)

        joined_hashranges = [y for x in complete_hash_list for y in x]

        # remove duplicate hashes
        collapsed_ranges = list(set(joined_hashranges))

        # sort the range list for good measure
        collapsed_ranges.sort()

        # first hash in the list is 0?
        if collapsed_ranges[0] != 0:
            self.logger.error(f"First hash in range ({collapsed_ranges[0]}) "
                              "is not zero")
            return False

        # last hash in the list is 32-bits high?
        if collapsed_ranges[-1] != int(0xffffffff):
            self.logger.error("Last hash in ranges "
                              f"({hex(collapsed_ranges[-1])}) is not "
                              "0xffffffff")
            return False

        # remove the first and last hashes
        clipped_ranges = collapsed_ranges[1:-1]

        # walk through the list in pairs and look for diff == 1
        iter_ranges = iter(clipped_ranges)
        for first in iter_ranges:
            second = next(iter_ranges)
            hash_difference = second - first
            if hash_difference > 1:
                self.logger.error("Layout has holes")
                return False
            elif hash_difference < 1:
                self.logger.error("Layout has overlaps")
                return False

        return True

    @staticmethod
    def create_brickpathlist(subvols: list, path: str) -> list:
        """
        Args:
            subvols(list): List of subvols
            path (str): Path/name of file under brick

        Return Value:
            List of brick path to the file
            Note: Only one brick is accounted from one subvol.
        """
        secondary_bricks = []
        for subvol in subvols:
            secondary_bricks.append(subvol[0])

        brickpathlist = []
        for item in secondary_bricks:
            brickpathlist.append(f"{item}/{path}")

        return brickpathlist

    def calculate_hash(self, host: str, filename: str) -> int:
        """
        Function to import DHT Hash library.

        Args:
            host (str): Node on which hash will be calculated
            filename (str): the name of the file

        Returns:
            An integer representation of the hash

        TODO: For testcases specifically testing hashing routine
              consider using a baseline external Davies-Meyer hash_value.c
              Creating comparison hash from same library we are testing
              may not be best practice here. (Holloway)
        """
        try:
            # Check if libglusterfs.so.0 is available locally
            glusterfs = ctypes.cdll.LoadLibrary("libglusterfs.so.0")
            self.logger.debug("Library libglusterfs.so.0 loaded locally")
            computed_hash = (ctypes.c_uint32(glusterfs.gf_dm_hashfn(filename,
                             len(filename))))
            hash_value = int(computed_hash.value)
        except OSError:
            cmd = f"python3 /tmp/compute_hash.py {filename}"
            ret = self.execute_abstract_op_node(cmd, host, False)
            if ret['error_code'] != 0:
                self.logger.error(f"Unable to run the script on node: {host}")
                return 0

            out = " ".join(ret['msg'])
            hash_value = int(out.split('\n')[0])
        return hash_value

    def find_specific_hashed(self, subvols_list: list, parent_path: str,
                             subvol: str, existing_names=None) -> tuple:
        """
        Finds filename that hashes to a specific subvol.

        Args:
            subvols_list(list): list of subvols
            parent_path(str): parent path (relative to mount) of "oldname"
            subvol(str): The subvol to which the new name has to be hashed
            existing_names(int|list): The name(s) already hashed to subvol

        Returns:
            A tuple (name, brickdir_path, count) containing
                name: Newname of hashed object
                brickdir_path: Brick path for which new hash was calculated
                count: Subvol count
            Or, None in case of failure or if hash not found
        Note: The new hash will be searched under the same parent
        """
        if not isinstance(existing_names, list):
            existing_names = [existing_names]

        bricklist = self.create_brickpathlist(subvols_list, parent_path)
        if not bricklist:
            self.logger.error("Could not form brickpath list")
            return None

        count = -1
        for item in range(1, 5000):
            host, _ = bricklist[0].split(':')
            newhash = self.calculate_hash(host, str(item))
            for brickdir in bricklist:
                count += 1
                _, subvol_path = subvol.split(':')
                brickhost, brickpath = brickdir.split(':')
                if (subvol_path == brickpath and item not in existing_names):
                    ret = self.hashrange_contains_hash(brickdir, newhash)
                    if ret:
                        self.logger.debug(f"oldhashed {subvol_path} new "
                                          f"{brickhost} count {count}")
                        return (item, brickdir, count)
            count = -1
        return None

    def find_hashed_subvol(self, subvols_list: list, parent_path: str,
                           name: str) -> tuple:
        """
        Args:
            subvols_list (list):  Subvols list
            parent_path (str): Immediate parent path of "name" relative from
                         mount point
                         e.g. if your mount is "/mnt" and the path from mount
                         is "/mnt/directory" then just pass "directory" as
                         parent_path
            name (str): file or directory name

        Return Values:
            A tuple (hashed_subvol, subvol_count) where the values are
                hashed_subvol: The hashed subvolume
                subvol_count: The subvol index in the subvol list
            Or, None on failure
        """
        if not isinstance(subvols_list, list):
            subvols_list = [subvols_list]

        bricklist = self.create_brickpathlist(subvols_list, parent_path)
        if not bricklist:
            self.logger.error("Could not form brickpath list")
            return None

        host, _ = bricklist[0].split(':')
        hash_num = self.calculate_hash(host, name)

        count = -1
        for brickdir in bricklist:
            count += 1
            ret = self.hashrange_contains_hash(brickdir, hash_num)
            if ret:
                self.logger.debug(f"Hash subvolume is {host}")
                hashed_subvol = brickdir
                break

        return hashed_subvol, count
