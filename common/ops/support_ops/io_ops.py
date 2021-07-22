"""
This file contains one class - IoOps which
holds API for running all the IO commands.
"""
import os
import re
from common.ops.abstract_ops import AbstractOps


# pylint: disable=too-many-lines
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

    def remove_file(self, host: str, fqpath: str,
                    force: bool = False) -> bool:
        """
        Removes a remote file.

        Args:
            host (str): The hostname/ip of the remote system.
            fqpath (str): The fully-qualified path to the file.

        Returns:
            True on success. False on fail.
        """
        cmd = "rm"
        if force:
            cmd += " -f"

        cmd += f" {fqpath}"
        ret = self.execute_abstract_op_node(cmd, host, False)
        if ret['error_code'] != 0:
            self.logger.error(f"Failed to remove file: {ret['error_msg']}")
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

    def append_string_to_file(self, node: str, filename: str, str_to_add: str,
                              user='root') -> bool:
        """
        Apeends the given string in the file

        Args:
            node (str): Node on which the command has to be executed
            filename (str): absolute file path to append the string
            str_to_add_in_file (str): string to be added in the file,
                    which is used as a start and stop string for parsing
                    the file in search_pattern_in_file().

        Optional:
            user (str): username. Defaults to 'root' user.

        Returns:
            bool: True, on success, False otherwise
        """
        cmd = f"echo '{str_to_add}' >> {filename}"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            self.logger.error(f"Unable to append string '{str_to_add}' "
                              f"to file {filename} using user {user}")
            return False

        return True

    def get_dir_contents(self, path: str, node: str,
                         recursive: bool = False) -> list:
        """
        Get the files and directories present in a given directory.

        Args:
            path (str): The path to the directory.
            node (str): IP of the remote system.

        Optional:
            recursive (bool): lists all entries recursively

        Returns:
            file_dir_list (list): List of files and directories on path.
            None: In case of error or failure.
        """
        if recursive:
            cmd = f"find {path}"
        else:
            cmd = f"ls {path}"

        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code']:
            self.logger.error(f"Unable to list directory contents for {path}:"
                              f" {ret['error_msg']}")
            return None

        out = "".join(ret['msg'])
        return list(filter(None, out.split("\n")))

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

    def create_files(self, fix_fil_size: str, path: str, node: str,
                     num_files: int = 1,
                     base_file_name: str = "testfile",
                     file_type: str = "txt") -> dict:
        """
        Create files with fixed size. This function encapsulates the
        operation of the file_dir_ops script present in the client machines.
        Args:
            fix_fil_size (str): Size of the file
            path (str) : Path wherein this io is to be done.
            node (str): Node on which command has to execute
            num_files (int): Number of files to be created recursively
                             under 'dir'
            base_file_name (str): Base file name
            file_type (str): Type of file to create
        Returns:
            async_object
        """
        cmd = (f"python3 /tmp/file_dir_ops.py create_files "
               f"-f {num_files} --fixed-file-size {fix_fil_size} "
               f"--base-file-name {base_file_name} "
               f"--file-types {file_type} {path}")
        return self.execute_command_async(cmd, node)

    def create_deep_dirs_with_files(self, path: str, dir_start_no: int,
                                    dir_depth: int, dir_length: int,
                                    max_no_dirs: int, no_files: int,
                                    node: str) -> dict:
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

    def set_file_permissions(self, node: str, fqpath: str, perms: str):
        """Set permissions on a remote file.

        Args:
            node (str): The node on which command has to execute
            fqpath (str): The fully-qualified path to the file.
            perms (str): A permissions string as passed to chmod.

        Returns:
            True on success. False on fail.
        """
        cmd = f"chmod {perms} {fqpath}"
        ret = self.execute_abstract_op_node(cmd, node, False)

        if ret['error_code'] == 0:
            return True

        self.logger.error(f"chmod failed: {ret['error_msg']}")
        return False

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
            cmd = f"arequal-checksum {total_path}"
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

    def get_fattr_list(self, fqpath: str, node: str,
                       encode_hex=False) -> dict:
        """
        List of xattr for filepath on remote system.
        Args:
            fqpath (str): The fully-qualified path to the file.
            node (str): The hostname/ip of the remote system.
        Kwargs:
        encode_hex(bool): Fetch xattr in hex if True
                            (Default:False)
        Returns:
            xattr_list (dict): dict of xattr values.
        """

        cmd = f"getfattr --absolute-names -d -m - {fqpath}"
        if encode_hex:
            cmd = f"getfattr --absolute-names -d -m - -e hex {fqpath}"

        ret = self.execute_abstract_op_node(cmd, node)

        xattr_list = {}
        ret_val = "".join(ret['msg'])
        for xattr_string in ret_val.strip().split('\n'):
            xattr = xattr_string.split('=', 1)
            if len(xattr) > 1:
                key, value = xattr
                xattr_list[key] = value

        return xattr_list

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

    def check_if_pattern_in_file(self, node: str,
                                 pattern: str, fqpath: str):
        """Check if a give pattern is in seen in file or not.

        Args:
            node (str): The hostname/ip of the remote system.
            pattern(str): Pattern to be found in file.
            fqpath (str): The fully-qualified path to the file.

        Returns:
            0: If pattern present in file.
            1: If pattern not present in file.
           -1: If command was not executed.
        """
        cmd = f"cat {fqpath} | grep \"{pattern}\""
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            return -1
        if len(ret['msg']) == 0:
            return 1
        return 0

    def find_and_replace_in_file(self, node: str,
                                 fpattern: str, rpattern: str,
                                 fqpath: str):
        """Find and replace all occurances of a given pattern in a specific file.

        Args:
            node (str): The node on which the command has to be executed.
            fpattern(str): Pattern to be found in file.
            rpattern(str): Pattern to used as replacement in file.
            fqpath (str): The fully-qualified path to the file.

        Returns:
            True: If find and replace is successful.
            False: If find and replace is failed.
        Note:
        / can't be given as an input in patterns(fpattern/rpattern).
        Please follow proper regex format for patterns.
        """
        cmd = f"sed -i 's/{fpattern}/{rpattern}/g' {fqpath}"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            return False
        return True

    def move_file(self, node: str, source_fqpath: str,
                  dest_fqpath: str) -> bool:
        """Move a remote file.

        Args:
            node (str): The hostname/ip of the remote system.
            source_fqpath (str): The fully-qualified path to
                                 the file to move.
            dest_fqpath (str): The fully-qualified path to the new
                               file location.

        Returns:
            True on success. False on fail.
        """
        cmd = f"mv {source_fqpath} {dest_fqpath}"
        ret = self.execute_abstract_op_node(cmd, node, False)

        if ret['error_code'] == 0:
            return True
        return False

    def add_user(self, servers: str, username: str,
                 group: str = None) -> bool:
        """
        Add user with default home directory

        Args:
            servers(list|str): hostname/ip of the system
            username(str): username of the user to be created.
            group(str): Group name to which user is to be
                        added.(Default:None)

        Returns:
            bool : True if user add is successful on all servers.
                   False otherwise.
        """
        # Checking if group is given or not
        if not group:
            cmd = f"useradd -m {username} -d /home/{username}"
        else:
            cmd = f"useradd -G {group} {username}"

        if not isinstance(servers, list):
            servers = [servers]

        results = self.execute_abstract_op_multinode(cmd, servers,
                                                     False)
        for result in results:
            if (result['error_code'] != 0
               and "already exists" not in result['error_msg']):
                self.logger.error("Unable to add user "
                                  f"on {result['node']}")
                return False
        return True

    def del_user(self, servers: str, uname: str) -> bool:
        """
        Delete user with home directory

        Args:
            servers (str|list): list of hostname/ip of the system
            uname (str): username

        Returns:
        True if user delete is successful on all servers.
        False otherwise.
        """
        cmd = f"userdel -r {uname}"

        if not isinstance(servers, list):
            servers = [servers]

        results = self.execute_abstract_op_multinode(cmd, servers,
                                                     False)
        for result in results:
            if (result['error_code'] != 0
               and "does not exist" not in result['error_msg']):
                self.logger.error("Unable to delete user "
                                  f"on {result['node']}")
                return False
        return True

    def group_add(self, servers: list, groupname: str) -> bool:
        """
        Creates a group in all the servers.

        Args:
            servers(list|str): Nodes on which cmd is to be executed.
            groupname(str): Name of the group to be created.

        Returns:
            bool: True if add group is successful on all servers.
                  False otherwise.
        """
        if not isinstance(servers, list):
            servers = [servers]

        cmd = f"groupadd {groupname}"
        results = self.execute_abstract_op_multinode(cmd, servers,
                                                     False)

        for result in results:
            if (result['error_code'] != 0
               and "already exists" not in result['error_msg']):
                self.logger.error(f"Unable to add group {groupname} "
                                  f"on {result['node']}")
                return False
        return True

    def group_del(self, servers: list, groupname: str) -> bool:
        """
        Deletes a group in all the servers.

        Args:
            servers(list|str): Nodes on which cmd is to be executed.
            groupname(str): Name of the group to be removed.

        Returns:
            bool: True if delete group is successful on all servers.
                  False otherwise.
        """
        if not isinstance(servers, list):
            servers = [servers]

        cmd = f"groupdel {groupname}"
        results = self.execute_abstract_op_multinode(cmd, servers,
                                                     False)

        for result in results:
            if (result['error_code'] != 0
               and "does not exist" not in result['error_msg']):
                self.logger.error(f"Unable to delete group {groupname} "
                                  f"on {result['node']}")
                return False
        return True

    def get_pathinfo(self, fqpath: str, node: str) -> dict:
        """
        Get pathinfo for a remote file.

        Args:
            fqpath (str): The fully-qualified path to the file.
            node (str): The hostname/ip of the remote system.

        Returns:
            A dictionary of pathinfo data for a remote file. None on fail.
        """
        pathinfo = {}
        pathinfo['raw'] = self.get_fattr(fqpath,
                                         'trusted.glusterfs.pathinfo',
                                         node, encode="text")
        pathinfo['brickdir_paths'] = re.findall(r".*?POSIX.*?:(\S+)\>",
                                                pathinfo['raw'])

        return pathinfo

    def rmdir(self, fqpath: str, node: str, force: bool = False) -> bool:
        """Removes a directory.

        Args:
            fqpath (str): The fully-qualified path to the file.
            node (str): The hostname/ip of the remote system.

        Optional:
            force (bool): Remove directory with recursive file delete.
        Returns:
            True on success. False on failure.
        """
        cmd = "rmdir"
        if force:
            cmd = "rm"
            cmd = f"{cmd} -rf"

        cmd = f"{cmd} {fqpath}"
        ret = self.execute_abstract_op_node(cmd, node, False)

        if ret['error_code'] != 0:
            self.logger.error("Directory remove failed")
            return False

        return True

    def list_files(self, node: str, dir_path: str, parse_str: str = "",
                   user: str = "root") -> list:
        """
        This module list files from the given file path

        Example:
            list_files("/root/dir1/")

        Args:
            node (str): Node on which cmd has to be executed.
            dir_path (str): directory path name

        Optional:
            parse_str (str): sub string of the filename to be fetched
            user (str): username. Defaults to 'root' user.

        Returns:
            list: files with absolute name
            NoneType: None if command execution fails, parse errors.
        """
        if parse_str == "":
            cmd = f"find {dir_path} -type f"
        else:
            cmd = f"find {dir_path} -type f | grep {parse_str}"

        # TODO: add user as currently it defaults to root in the
        # framework
        ret = self.execute_abstract_op_node(cmd, node)
        if ret['error_code'] != 0:
            self.logger.error("Unable to get the list of files on path "
                              f"{dir_path} on node {node} for user {user}")
            return None
        return ret['msg']

    def create_link_file(self, node: str, sfile: str, link: str,
                         soft: bool = False) -> bool:
        """
        Create hard or soft link for an exisiting file

        Args:
            node(str): Host on which the command is executed.
            sfile(str): Path to the source file.
            link(str): Path to the link file.

        Optional:
            soft(bool): Create soft link if True else create
                        hard link.

        Returns:
            (bool): True if command successful else False.

        Example:
            >>> create_link_file('XX.YY.30.40', '/mnt/mp/file.txt',
                                '/mnt/mp/link')
            True
        """
        cmd = f"ln {sfile} {link}"
        if soft:
            cmd = f"{cmd} -s"

        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            if soft:
                self.logger.error('Failed to create soft link on '
                                  f'{node} for file {sfile}')
            else:
                self.logger.error('Failed to create hard link on '
                                  f'{node} for file {sfile}')
            return False
        return True

    def kill_process(self, node: str, process_ids: str = '',
                     process_names: str = '') -> bool:
        """
        Kills the given set of process running in the specified node

        Args:
            node (str): Node at which the command has to be executed
            process_ids (list|str): List of pid's to be terminated
            process_names(list|str): List of Process names to be terminated

        Returns:
            bool : True on successful termination of all the processes
                   False, otherwise
        Example:
            >>> kill_process("10.70.43.68", process_ids=27664)
            True/False
            >>> kill_process("10.70.43.68", process_names=["glustershd",
            "glusterd"])
            True/False
        """
        if process_names:
            process_ids = []
            if not isinstance(process_names, list):
                process_names = [process_names]

            for process in process_names:
                cmd = (f"ps -aef | grep -i '{process}' | grep -v 'grep' | "
                       "awk '{ print $2 }'")
                ret = self.execute_abstract_op_node(cmd, node, False)
                if ret['error_code'] != 0:
                    self.logger.error("Failed to get the PID for process")
                    return False

                for pid in ret['msg']:
                    if pid:
                        process_ids.append(pid.rstrip('\n'))

        if process_ids and not isinstance(process_ids, list):
            process_ids = [process_ids]

        # Kill process
        for pid in process_ids:
            ret = self.execute_abstract_op_node(f"kill -9 {pid}", node, False)
            if ret['error_code'] != 0:
                self.logger.error(f"Failed to kill process with pid {pid}")
                return False

        return True
