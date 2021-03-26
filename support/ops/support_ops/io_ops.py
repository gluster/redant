"""
This file contains one class - io_ops which
holds IO related APIs which will be called
from the test case.
"""


class io_ops:
    """
    io_ops class provides APIs to perform operations
    like creating files and directories,listing the directory
    contents and to handle non-standard IO commands.
    """

    def touch(self, node: str, file_path: str):
        """
        Creates a regular empty file

        Args:
            node (str): The node in the cluster where the command is to be run
            file_path (str): The name of the file to be created            
        """

        cmd = f"touch {file_path}"

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")


    def mkdir(self, node: str, dir_path: str, parents: bool=False, mode: str=None):
        '''
        Creates a directory

        Args:
            node (str): The node in the cluster where the command is to be run
            dir_path (str): The name of the directory to be created
            parents (bool, optional): Create parent directories if do not exist.
            mode (str, optional): The initial mode of the directory.
        '''

        cmd_list = ['mkdir']
        if parents:
            cmd_list.append('-p')
        if mode is not None:
            cmd_list.append(f'-m {mode}')
        cmd_list.append(dir_path)

        cmd = ' '.join(cmd_list)

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")


    def rmdir(self, node: str, dir_path: str, force: bool=False):
        """
        Remove a directory.

        Args:
            node (str): The hostname of the node where command is to be run.
            dir_path (str): The path to the file.
            force (bool, optional): Remove directory with recursive file delete.
        """
        cmd_list = ['rmdir']
        if force:
            cmd_list = ["rm"]
            cmd_list.append('-rf')
        cmd_list.append(dir_path)

        cmd = ' '.join(cmd_list)

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog("Successfully ran {cmd} on {node}")


    def ls(self, node: str, path: str):
        '''
        List the directory contents

        Args:
            node (str): The node in the cluster where the command is to be run
            path (str): Lists all files in the current directory path
        '''

        cmd = f'ls {path}'

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")


    def file_exists(self, node: str, file_path: str):
        """
        Check if file exists at path on node

        Args:
            node (str): The hostname of the node  on which command is to be run
            file_path (str): The path of the file
        """
    
        cmd = f"ls -ld {file_path}"

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog("Successfully ran {cmd} on {node}")


    def run(self, node: str, cmd: str):
        '''
        Used for non-standard IO commands

        Args:
            node (str): The node in the cluster where the command is to be run
            cmd (str): The non-standard command which is to be run
        '''

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")
