"""
This file contains one class - IoOps which
holds API for running all the IO commands.
"""
import os
import re
from common.ops.abstract_ops import AbstractOps


class IoOps(AbstractOps):
    """
    IoOps class provides API to handle
    all the IO commands. The io_commands are divided
    into 2 categories - one is the normal io ops and
    the other the io_ops which execute on mountpoints.
    """

    def create_file(self, path: str, filename: str, node: str) -> bool:
        """
        Creates a file in the specified specified path
        Args:
            path (str): The path where the file has to be
                  created
            filename (str): Name of the file
            node (str): The node on which command
                        has to run.
        Returns:
            True if file is successfully created or already present and false
            if file creation failed.
        """
        cmd = f"touch {path}/{filename}"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            return False
        return True

    def create_dir(self, path: str, dirname: str, node: str,
                   excep: bool = True) -> dict:
        """
        Creates a directory in the specified path
        Args:
            path (str): The path where the file has to be
                  created
            dirname (str): Name of the directory
            node (str): The node on which command
                        has to run.
            excep (bool): Whether to bypass the exception handling in
                          abstract ops.
        Returns:
            ret_dict returned by the abstract ops.
        """
        cmd = f"mkdir -p {path}/{dirname}"
        return self.execute_abstract_op_node(cmd, node, excep)

    def create_dirs(self, list_of_nodes: list,
                    list_of_dir_paths: list) -> bool:
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

    def path_exists(self, list_of_nodes: list, list_of_paths: list) -> bool:
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

        for path in list_of_paths:
            cmd = f"stat {path}"
            ret = self.execute_command_multinode(cmd, list_of_nodes)
            for each_ret in ret:
                if each_ret['error_code'] != 0:
                    error_string = each_ret['error_msg'].rstrip('\n')
                    self.logger.error(f"{error_string} on node "
                                      f"{each_ret['node']}")
                    return False

        return True

    def get_file_stat(self, node: str, path: str) -> str:
        """
        Function to get file stat.
        Args:
            node (str)
            path (str)
        Returns:
            Dictionary of the form,
            {
              "error_code" : 0/something else,
              "msg" : DICT or string of error
            }
        """
        ret_val = {'error_code': 0, 'msg': ''}
        cmd = (f"python3 /tmp/file_dir_ops.py stat {path}")
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            ret_val['error_code'] = ret['error_code']
            ret_val['msg'] = ret['error_msg']
            return ret_val
        tmp_msg = ret['msg'][2:-3]
        tmp_msg = tmp_msg[0][tmp_msg[0].find('{'):-1]
        stat_res = {}
        for list_val in tmp_msg.split(','):
            tmp_val = list_val.split(':')
            if len(tmp_val) == 1:
                tmp_val = list_val.split('=')
            if tmp_val[0].find('{') >= 0:
                tmp_val[0] = tmp_val[0][1:]
            if tmp_val[1].find('}') >= 0:
                tmp_val[1] = tmp_val[1][:-1]
            if tmp_val[1].find(')') >= 0:
                tmp_val[1] = tmp_val[1][:-1]
            tmp_val[0] = tmp_val[0].strip().replace("'", "")
            tmp_val[1] = tmp_val[1].strip().replace("'", "")
            if tmp_val[0] == 'stat':
                tmp_val[0] = tmp_val[1][15:].split('=')[0]
                tmp_val[1] = tmp_val[1][15:].split('=')[1]
            if tmp_val[1].isdigit():
                tmp_val[1] = float(tmp_val[1])
                if tmp_val[1].is_integer():
                    tmp_val[1] = int(tmp_val[1])
            stat_res[tmp_val[0]] = tmp_val[1]
        ret_val['msg'] = stat_res
        return ret_val

    def create_deep_dirs_with_files(self, path: str, dir_start_no: int,
                                    dir_depth: int, dir_length: int,
                                    max_no_dirs: int, no_files: int,
                                    node: str):
        """
        Create deep directories and files. This function encapsulates the
        operation of the file_dir_ops script present in the client machines.
        Args:
            path (str) : Path wherein this io is to be done.
            dir_start_no (int) : From which number, the dir numbering will be
                                 started
            dir_depth (int) : The depth till which dirs have to be created.
            dir_length (int) : The number of dirs at the top level.
            max_no_dirs (int) : The number of dirs in a level.
            no_files (int) : The number of files to be created under a
                             directory.
            node (str) : Node wherein the commad has to be run.
        Returns:
            async_object
        """
        cmd = (f"python3 /tmp/file_dir_ops.py create_deep_dirs_with_files "
               f"--dirname-start-num {dir_start_no} --dir-depth {dir_depth}"
               f" --dir-length {dir_length} --max-num-of-dirs {max_no_dirs} "
               f"--num-of-files {no_files} {path}")
        return self.execute_command_async(cmd, node)

    def get_file_permission(self, node: str, path: str) -> dict:
        """
        Function to get file permissions.

        Args:
            node (str)
            path (str)
        Returns:
            Dictionary has the following key-value pairs
            1. error_code (int): 0 being success.
            2. file_perm (int): valid file permission or 0 for error.
        """
        ret_val = {}
        cmd = f'stat -c "%a" {path}'
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            ret_val['error_code'] = ret['error_code']
            ret_val['file_perm'] = 0
            return ret_val
        ret_val['error_code'] = ret['error_code']
        ret_val['file_perm'] = int(ret['msg'][0][:-1])
        return ret_val

    def check_core_file_exists(self, nodes: list, testrun_timestamp,
                               paths=['/', '/var/log/core',
                                      '/tmp', '/var/crash', '~/']):
        '''
        Listing directories and files in "/", /var/log/core, /tmp,
        "/var/crash", "~/" directory for checking if the core file
        created or not

        Args:

            nodes(list):
                List of nodes need to pass from test method
            testrun_timestamp:
                This time stamp need to pass from test method
                test case running started time, time format is EPOCH
                time format, use below command for getting timestamp
                of test case 'date +%s'
            paths(list):
                By default core file will be verified in "/","/tmp",
                "/var/log/core", "/var/crash", "~/"
        Return:
         bool : True if core file was created
                else False
        If test case need to verify core file in specific path,
        need to pass path from test method
        '''
        count = 0
        cmd_list = []
        for path in paths:
            cmd = ' '.join(['cd', path, '&&', 'ls', 'core*'])
            cmd_list.append(cmd)

        # Checks for core file in "/", "/var/log/core", "/tmp" "/var/crash",
        # "~/" directory
        for node in nodes:
            cmd = 'grep -r "time of crash" /var/log/glusterfs/'
            try:
                ret = self.execute_abstract_op_node(cmd, node)
                logfiles = " ".join(ret['msg'])
                if ret['error_code'] == 0:
                    self.logger.error(" Seems like there was a crash,"
                                      " kindly check the logfiles, "
                                      "even if you don't see a core file")
                for logfile in logfiles.strip('\n').split('\n'):
                    self.logger.error(f"Core was found in "
                                      f"{logfile.split(':')[0]}")
            except Exception as error:
                self.logger.info(f"Error: {error}")

            for cmd in cmd_list:
                try:
                    ret = self.execute_abstract_op_node(cmd, node)
                    out = " ".join(ret['msg'])
                    self.logger.info("storing all files and directory "
                                     "names into list")
                    dir_list = re.split(r'\s+', out)

                    # checking for core file created or not in "/"
                    # "/var/log/core", "/tmp" directory
                    self.logger.info("checking core file created or not")
                    for file1 in dir_list:
                        if re.search(r'\bcore\.[\S]+\b', file1):
                            file_path_list = re.split(r'[\s]+', cmd)
                            file_path = file_path_list[1] + '/' + file1
                            time_cmd = 'stat ' + '-c ' + '%X ' + file_path
                            ret = self.execute_abstract_op_node(time_cmd, node)
                            file_timestamp = ret['msg'][0].rstrip('\n')
                            file_timestamp = file_timestamp.strip()
                            if file_timestamp > testrun_timestamp:
                                count += 1
                                self.logger.error(f"New core file was created "
                                                  f"and found at {file1}")
                            else:
                                self.logger.info("Old core file Found")
                except Exception as error:
                    self.logger.info(f"Error: {error}")
        # return the status of core file
        if count >= 1:
            self.logger.error("Core file created glusterd crashed")
            return True
        else:
            self.logger.info("No core files found ")
            return False

    def collect_mounts_arequal(self, mounts: dict, path='') -> list:
        """
        Collects arequal from all the mounts
        Args:
            mounts (list): List of all mountpoints for checking arequal.
        Kwargs:
            path (str): Path whose arequal is to be calculated.
                        Defaults to root of mountpoint
        Returns:
            list:
                list of arequal-checksums of each mount
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
        error_msg = ""
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"Collecting arequal-checksum failed on "
                                  f"{mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']}")
                _rc = False
                error_msg = ret['error_msg']
                all_mounts_arequal_checksums.append(None)
            else:
                all_mounts_arequal_checksums.append(ret["msg"])
        if not _rc:
            raise Exception(error_msg)
        return all_mounts_arequal_checksums

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

    def get_mounts_stat(self, mounts: list) -> list:
        """
        Recursively get stat of the mountpoint
        Args:
            mounts (list): List of all mountpoints.
        Returns:
            list: list of attributes of stat command
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
        error_msg = ""
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"Stat of files and dirs under "
                                  f"{mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']} Failed")
                _rc = False
                error_msg = ret['error_msg']

        if not _rc:
            raise Exception(error_msg)
        return ret['msg']

    def list_all_files_and_dirs_mounts(self, mounts: list) -> bool:
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
        error_msg = ""
        for i, async_obj in enumerate(all_mounts_async_objs):
            ret = self.wait_till_async_command_ends(async_obj)
            if ret['error_code'] != 0:
                self.logger.error(f"Failed to list all files and dirs under "
                                  f"{mounts[i]['client']}:"
                                  f"{mounts[i]['mountpath']}")
                _rc = False
                error_msg = ret['error_msg']
        if not _rc:
            raise Exception(error_msg)
        return _rc

    # TODO: Test the below function when snaphot library is added.
    def view_snaps_from_mount(self, mounts: list, snaps: list) -> list:
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
        if not _rc:
            raise Exception("Failed to list snaps for some mountpoints")
        return _rc

    def validate_io_procs(self, all_mounts_async_objs: list,
                          mounts: list) -> bool:
        """
        Validate whether IO was successful or not.
        Args:
            all_mounts_async_objs (list): List of open connection descriptor
                                          as returned by
                                          self.execute_command_async method.
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
            return True
        return False

    def wait_for_io_to_complete(self, all_mounts_async_objs: list,
                                mounts: list) -> bool:
        """
        Waits for IO to complete
        Args:
            all_mounts_async_objs (list): List of open connection descriptor
                                          as returned by g.run_async method.
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

    def cleanup_mounts(self, mounts: list) -> bool:
        """
        Removes all the data from all the mountpoints
        Args:
            mounts (list): List of all GlusterMount objs.
        Returns:
            bool: True if cleanup is successful on all mounts
                  False otherwise.
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

    def compare_dir_structure_mount_with_brick(self, mnthost: str,
                                               mntloc: str,
                                               brick_list: list,
                                               perm_type: int) -> bool:
        """
        Compare mount point dir structure with brick path along
        with stat param.
        Args:
            mnthost (str): hostname or ip of mnt system
            mntloc (str) : mount location of gluster file system
            brick_list (list) : list of all brick ip's with brick path
            perm_type  (int) : 0 represent user permission
                        : 1 represent group permission
                        : 2 represent access permission
        Returns:
            bool: True if directory structure are same,
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

    def run_linux_untar(self, clients: list, mountpoint: str,
                        dirs: tuple = ('.')) -> list:
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
                       f"{mountpoint}/{directory}")
                self.execute_abstract_op_node(cmd, client)

                # Start linux untar
                cmd = ("cd {}/{}; tar -xvf linux-5.4.54.tar.xz"
                       .format(mountpoint, directory))
                async_obj = self.execute_command_async(cmd, client)
                list_of_procs.append(async_obj)

        return list_of_procs

    def get_fattr(self, fpath: str, fattr: str, node: str,
                  encode: str = "hex") -> list:
        """
        Function to get the fattr on a said file on a remote folder.

        Args:
            1. fpath (str): The file path wherein the fattr is to be checked.
            2. fattr (str): The fattr name to be checked.
            3. node (str): The node wherein the fattr is to be checked.
            4. encode (str): Optional parameter with default value of 'hex'.
                             The encoding in which the return value s required.
        Returns:
            getfattr result on success. Exception thrown on failure.
        """
        cmd = (f"getfattr --absolute-names -e '{encode}' -n '{fattr}' {fpath}")
        ret = self.execute_abstract_op_node(cmd, node)
        return ret['msg']

    def set_fattr(self, fpath: str, fattr: str, node: str, value: str) -> list:
        """
        Function to set fattr on a path.

        Args:
            1. fpath (str): The file path wherein the fattr is to be set.
            2. fattr (str): The fattr name to be set.
            3. node (str): Node wherein the fattr is to be checked.
            4. value (str): value to be set.
        Returns:
            setfattr result or exception will be raised on failure.
        """
        cmd = (f"setfattr -n {fattr} -v {value} {fpath}")
        ret = self.execute_abstract_op_node(cmd, node)
        return ret['msg']

    def delete_fattr(self, fpath: str, fattr: str, node: str) -> list:
        """
        Function to delete fattr set on a path.

        Args:
            1. fpath (str): The file path wherein the fattr is to be set.
            2. fattr (str): The fattr to be delete
            3. node (str): Node wherein the fattr is to be set.
        Returns:
            The setfattr result or exception will be raised on failure.
        """
        cmd = (f"setfattr -x {fattr} {fpath}")
        ret = self.execute_abstract_op_node(cmd, node)
        return ret['msg']
