"""
DHT ops contain methods which deals with DHT operations like
hashing, layout and so on.
"""

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
