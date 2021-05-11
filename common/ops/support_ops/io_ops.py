"""
This file contains one class - IoOps which
holds API for running all the IO commands.
"""
import os
from common.ops.abstract_ops import AbstractOps


class IoOps(AbstractOps):
    """
    IoOps class provides API to handle
    all the IO commands. The io_commands are divided
    into 2 categories - one is the normal io ops and
    the other the io_ops which execute on mountpoints.
    """

    def execute_io_cmd(self, cmd: str, host: str = None):
        '''
        Used for all the IO commands

        Args:
            cmd (str): The IO command which is to be run
            host (str): The node in the cluster where the command is to be run

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        '''

        ret = self.execute_abstract_op_node(cmd, host)

        return ret

    def create_file(self, path: str, filename: str, node: str):
        """
        Creates a file in the specified specified path
        Args:
            path (str): The path where the file has to be
                  created
            filename (str): Name of the file
            node (str): The node on which command
                        has to run.
        """
        cmd = f"touch {path}/{filename}"
        self.execute_abstract_op_node(cmd, node)

    def create_dir(self, path: str, dirname: str, node: str):
        """
        Creates a directory in the specified path
        Args:
            path (str): The path where the file has to be
                  created
            dirname (str): Name of the directory
            node (str): The node on which command
                        has to run.
        """
        cmd = f"mkdir -p {path}/{dirname}"
        self.execute_abstract_op_node(cmd, node)

    def create_dirs(self, list_of_nodes: list, list_of_dir_paths: list):
        """
        Create directories on nodes.
        Args:
            list_of_nodes (list): Nodes on which dirs has to be created.
            list_of_dir_paths (list): List of dirs abs path.
        Returns:
            bool: True of creation of all dirs on all nodes is successful.
                False otherwise.
        """
        if not isinstance(list_of_nodes, list):
            list_of_nodes = [list_of_nodes]

        if isinstance(list_of_dir_paths, list):
            list_of_dir_paths = ' '.join(list_of_dir_paths)

        # Create upload dir on each node
        cmd = f"mkdir -p {list_of_dir_paths}"
        _rc = True

        ret = self.execute_command_multinode(cmd, list_of_nodes)
        for each_ret in ret:
            if each_ret['error_code'] != 0:
                self.logger.error(f"Failed to create the dirs: "
                                  f"{list_of_dir_paths.split(' ')} "
                                  f"on node: {each_ret['node']} - "
                                  f"{each_ret['error_msg']}")
                _rc = False

        return _rc

    def path_exists(self, list_of_nodes, list_of_paths):
        """Check if paths exist on nodes.
        Args:
            list_of_nodes (list): List of nodes.
            list_of_paths (list): List of abs paths to verify if path exist.
        Returns:
            bool: True if all paths exists on all nodes. False otherwise.
        """
        if not isinstance(list_of_nodes, list):
            list_of_nodes = [list_of_nodes]

        if not isinstance(list_of_paths, list):
            list_of_paths = (list_of_paths.split(" "))

        _rc = True

        for path in list_of_paths:
            cmd = f"ls -l {path}"
            ret = self.execute_command_multinode(cmd, list_of_nodes)
        for each_ret in ret:
            if each_ret['error_code'] != 0:
                error_string = each_ret['error_msg'].rstrip('\n')
                self.logger.error(f"{error_string} on node {each_ret['node']}")
                _rc = False

        return _rc

    def collect_mounts_arequal(self, mounts: dict, path=''):
        """
        Collects arequal from all the mounts
        Args:
            mounts (list): List of all mountpoints for checking arequal.
        Kwargs:
            path (str): Path whose arequal is to be calculated.
                        Defaults to root of mountpoint
        Returns:
            tuple(bool, list):
                On success: (True, list of arequal-checksums of each mount)
                On failure: (False, list of arequal-checksums of each mount)
                arequal-checksum for a mount would be 'None' when failed to
                collect arequal for that mount.
        """

        # Collect arequal-checksum from all mounts
        self.logger.info("Start collecting arequal-checksum from all mounts")
        all_mounts_async_objs = []
        for mount in mounts:
            total_path = os.path.join(mount['mountpath'], path)
            self.logger.info(
                f"arequal-checksum of mount {mount['client']}:{total_path}")
            cmd = f"arequal-checksum -p {total_path} -i .trashcan"
            async_obj = self.execute_command_async(cmd, mount['client'])
            all_mounts_async_objs.append(async_obj)
        all_mounts_arequal_checksums = []
        _rc = True
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"Collecting arequal-checksum failed on "
                                  f"{mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']}")
                _rc = False
                all_mounts_arequal_checksums.append(None)
            else:
                self.logger.info(f"Collecting arequal-checksum successful on "
                                 f"{mounts[i]['client']}:"
                                 f"{mounts[i]['mountpath']}")
                all_mounts_arequal_checksums.append(ret["msg"])
        return (_rc, all_mounts_arequal_checksums)

    def log_mounts_info(self, mounts: list):
        """
        Log mount information like df, stat, ls
        Args:
            mounts (list): List of all GlusterMount objs.
        """

        self.logger.info("Start logging mounts information:")
        for mount in mounts:
            host = mount['client']
            mountpoint = mount['mountpath']
            self.logger.info(f"Information of mount {host}:{mountpoint}")

            # Mount Info
            self.logger.info("Look For Mountpoint:\n")
            cmd = (f"mount | grep {mountpoint}")
            ret = self.execute_abstract_op_node(cmd, host)
            self.logger.info(ret['msg'])

            # Disk Space Usage
            self.logger.info("Disk Space Usage Of Mountpoint:\n")
            cmd = (f"df -h {mountpoint}")
            ret = self.execute_abstract_op_node(cmd, host)
            self.logger.info(ret['msg'])

            # Long list the mountpoint
            self.logger.info("List Mountpoint Entries:\n")
            cmd = (f"ls -ld {mountpoint}")
            ret = self.execute_abstract_op_node(cmd, host)
            self.logger.info(ret['msg'])

            # Stat mountpoint
            self.logger.info("Mountpoint Status:\n")
            cmd = (f"stat {mountpoint}")
            ret = self.execute_abstract_op_node(cmd, host)
            self.logger.info(ret['msg'])

    def get_mounts_stat(self, mounts):
        """
        Recursively get stat of the mountpoint
        Args:
            mounts (list): List of all mountpoints.
        Returns:
            bool: True, if recursively getting stat from all
                        mounts is successful.
                  False otherwise.
        """

        self.logger.info("Start getting stat of the mountpoint recursively")
        all_mounts_async_objs = []
        for mount in mounts:
            self.logger.info(
                f"Stat of mount {mount['client']}:{mount['mountpath']}")
            cmd = f"find {mount['mountpath']} | xargs stat"
            async_obj = self.execute_command_async(cmd, mount['client'])
            all_mounts_async_objs.append(async_obj)
        _rc = True
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"Stat of files and dirs under "
                                  f"{mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']} Failed")
                _rc = False
        return _rc

    def list_all_files_and_dirs_mounts(self, mounts):
        """List all Files and Directories from mounts.
        Args:
            mounts (list): List of all GlusterMount objs.
        Returns:
            bool: True if listing file and dirs on mounts is successful.
                False otherwise.
        """

        ignore_dirs_list = [".trashcan"]
        ignore_dirs = r"\|".join(ignore_dirs_list)

        self.logger.info("Start Listing mounts files and dirs")
        all_mounts_async_objs = []
        for mount in mounts:
            self.logger.info(f"Listing files and dirs on {mount['client']}:"
                             f"{mount['mountpath']}")
            cmd = f"find {mount['mountpath']} | grep -ve '{ignore_dirs}'"
            async_obj = self.execute_command_async(cmd, mount['client'])
            all_mounts_async_objs.append(async_obj)
        _rc = True
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"Failed to list all files and dirs under "
                                  f"{mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']}")
                _rc = False
            else:
                self.logger.info(f"Successfully listed all files and dirs "
                                 f"under {mounts[i]['client']}:"
                                 f"{mounts[i]['mountpath']}")
        return _rc

    # TODO: Test the below function when snaphot library is added.
    def view_snaps_from_mount(self, mounts, snaps):
        """
        View snaps from the mountpoint under ".snaps" directory
        Args:
            mounts (list): List of all  mountpoints.
            snaps (list): List of snaps to be viewed from '.snaps' directory
        Returns:
            bool: True, if viewing all snaps under '.snaps' directory is
                        successful from all mounts.
                  False otherwise
        """

        if isinstance(mounts, dict):
            mounts = [mounts]

        if isinstance(snaps, str):
            snaps = [snaps]

        all_mounts_async_objs = []
        for mount in mounts:
            self.logger.info(f"Viewing '.snaps' on {mount['client']}:"
                             f"{mount['mountpath']}")
            cmd = f"ls -1 {mount['mountpath']}/.snaps"
            async_obj = self.execute_command_async(cmd, mount['client'])
            all_mounts_async_objs.append(async_obj)

        _rc = True
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"Failed to list '.snaps' on "
                                  f"{mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']} - "
                                  f"{ret['error_msg']}")
                _rc = False
            else:
                snap_list = ret['msg'].splitlines()
                if not snap_list:
                    self.logger.error(f"No snaps present in the '.snaps' "
                                      f"dir on {mounts[i]['client']}:"
                                      f"{mounts[i]['mountpath']}")
                    _rc = False
                    continue

                for snap_name in snaps:
                    if snap_name not in snap_list:
                        self.logger.error(f"Failed to list snap {snap_name} "
                                          f"in '.snaps' dir on "
                                          f"{mounts[i]['client']}:"
                                          f"{mounts[i]['mountpath']}"
                                          f" - {snap_list}")
                        _rc = False
                    else:
                        self.logger.info(f"Successful listed snap {snap_name}"
                                         f" in '.snaps' dir on "
                                         f"{mounts[i]['client']}:"
                                         f"{mounts[i]['mountpath']} "
                                         f"- {snap_list}")
        return _rc

    def validate_io_procs(self, all_mounts_async_objs, mounts):
        """
        Validate whether IO was successful or not.
        Args:
            all_mounts_async_objs (list): List of open connection descriptor as
                returned by self.execute_command_async method.
            mounts (list): List of all mountpoints on which process were
                started.
        Returns:
            bool: True if IO is successful on all mounts. False otherwise.
        """
        if not isinstance(all_mounts_async_objs, list):
            all_mounts_async_objs = [all_mounts_async_objs]

        if isinstance(mounts, dict):
            mounts = [mounts]

        _rc = True
        self.logger.info("Start validating IO procs")
        for i, async_obj in enumerate(all_mounts_async_objs):
            self.logger.info(f"Validating IO on {mounts[i]['client']}:"
                             f"{mounts[i]['mountpath']}")
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"IO Failed on {mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']}")
                _rc = False
        if _rc:
            self.logger.info("IO is successful on all mounts")
            return True
        return False

    def wait_for_io_to_complete(self, all_mounts_async_objs, mounts):
        """
        Waits for IO to complete
        Args:
            all_mounts_async_objs (list): List of open connection descriptor as
                returned by g.run_async method.
            mounts (list): List of all mountpoints on which process were
                started.
        Returns:
            bool: True if IO is complete on all mounts. False otherwise.
        """

        if isinstance(mounts, dict):
            mounts = [mounts]

        _rc = True
        for i, async_obj in enumerate(all_mounts_async_objs):
            self.logger.info(f"Waiting for IO to be complete on "
                             f"{mounts[i]['client']}:"
                             f"{mounts[i]['mountpath']}")
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"IO Not complete on {mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']}")
                _rc = False

        return _rc

    def cleanup_mounts(self, mounts):
        """
        Removes all the data from all the mountpoints
        Args:
            mounts (list): List of all GlusterMount objs.
        Returns:
            bool: True if cleanup is successful on all mounts. False otherwise.
        """
        if isinstance(mounts, dict):
            mounts = [mounts]

        self.logger.info("Start cleanup mounts")
        all_mounts_async_objs = []
        valid_mounts = []
        for mount in mounts:
            self.logger.info(f"Cleaning up data from {mount['client']}:"
                             f"{mount['mountpath']}")
            if (not mount['mountpath'] or (os.path.realpath(os.path.abspath(
                    mount['mountpath'])) == '/')):
                self.logger.error(f"{mount['mountpath']} on {mount['client']}"
                                  f" is not a valid mount point")
                continue
            cmd = f"rm -rf {mount['mountpath']}/*"
            async_obj = self.execute_command_async(cmd, mount['client'])
            all_mounts_async_objs.append(async_obj)
            valid_mounts.append(mount)
        self.logger.info(
            "rm -rf on all clients is complete. Validating deletion now...")

        # Get cleanup status
        _rc_rmdir = True
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0 or ret['msg'] or ('error_msg' in ret):
                self.logger.error(f"Deleting files/dirs Failed on "
                                  f"{valid_mounts[i]['client']}:"
                                  f"{valid_mounts[i]['mountpath']}")
                _rc_rmdir = False
        if not _rc_rmdir:
            self.logger.error(
                "Deleting files/dirs failed on some of the mounts")

        # Check if mount points are empty
        ignore_dirs_list = [".trashcan"]
        ignore_dirs = r"\|".join(ignore_dirs_list)
        all_mounts_async_objs = []
        for mount in mounts:
            cmd = (f"find {mount['mountpath']} -mindepth 1 | "
                   f"grep -ve '{ignore_dirs}'")
            async_obj = self.execute_command_async(cmd, mount['client'])
            all_mounts_async_objs.append(async_obj)

        # Get cleanup status
        _rc_lookup = True
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] == 0:
                self.logger.error(f"Mount {mounts[i]['mountpath']} on "
                                  f"{mounts[i]['client']} is still having"
                                  f" entries:\n{ret['msg']}")
                _rc_lookup = False
        if not _rc_lookup:
            self.logger.error("Failed to cleanup all mounts")

        return _rc_lookup

    def compare_dir_structure_mount_with_brick(self, mnthost, mntloc,
                                               brick_list, perm_type):
        """
        Compare mount point dir structure with brick path along
        with stat param.
        Args:
            mnthost (str): hostname or ip of mnt system
            mntloc (str) : mount location of gluster file system
            brick_list (list) : list of all brick ip's with brick path
            type  (int) : 0 represent user permission
                        : 1 represent group permission
                        : 2 represent access permission
        Returns:
            True if directory structure are same
            False if structure is not same
        """

        statformat = ''
        if perm_type == 0:
            statformat = '%U'
        if perm_type == 1:
            statformat = '%G'
        if perm_type == 2:
            statformat = '%A'

        cmd = (f"find {mntloc} -mindepth 1 -type d | "
               f"xargs -r stat -c '{statformat}'")
        ret = self.execute_abstract_op_node(cmd, mnthost)
        all_dir_mnt_perm = ret['msg']

        for brick in brick_list:
            brick_node, brick_path = brick.split(":")
            cmd = (f"find {brick_path} -mindepth 1 -type d | "
                   f"grep -ve \".glusterfs\" | "
                   f"xargs -r stat -c '{statformat}'")
            ret = self.execute_abstract_op_node(cmd, brick_node)
            all_brick_dir_perm = ret['msg']
            retval = (all_dir_mnt_perm > all_brick_dir_perm) - (
                all_dir_mnt_perm < all_brick_dir_perm)
            if retval != 0:
                return False

        return True

    def run_linux_untar(self, clients, mountpoint, dirs=('.')):
        """Run linux kernal untar on a given mount point
        Args:
        clients(str|list): Client nodes on which I/O
                            has to be started.
        mountpoint(str): Mount point where the volume is
                        mounted.
        Kwagrs:
        dirs(tuple): A tuple of dirs where untar has to
                        started. (Default:('.'))
        Returns:
        list: Returns a list of process object
        """
        # Checking and convering clients to list.
        if not isinstance(clients, list):
            clients = [clients]

        list_of_procs = []
        for client in clients:
            # Download linux untar to root, so that it can be
            # utilized in subsequent run_linux_untar() calls.
            cmd = ("wget https://cdn.kernel.org/pub/linux/kernel/"
                   "v5.x/linux-5.4.54.tar.xz")
            if not self.path_exists(client, '/root/linux-5.4.54.tar.xz'):
                self.execute_abstract_op_node(cmd, client)

            for directory in dirs:
                # copy linux tar to dir
                cmd = (f"cp /root/linux-5.4.54.tar.xz "
                       f"{mountpoint['mountpath']}/{directory}")
                self.execute_abstract_op_node(cmd, client)

                # Start linux untar
                cmd = ("cp /root/linux-5.4.54.tar.xz {}/{}"
                       .format(mountpoint['mountpath'], directory))
                async_obj = self.execute_command_async(cmd, client)
                list_of_procs.append(async_obj)

        return list_of_procs
