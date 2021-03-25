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

    def touch(self, file_path: str, node: str):
        """Creates a regular empty file
        Args:
            file_path (str): The name of the file to be created
            node (str): The node in the cluster where the command is to be run
        """

        cmd = f"touch {file_path}"

        self.rlog(f"Running {cmd} on node {node}")
        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog("Successfully ran {cmd} on {node}")

    def mkdir(self, dir_path: str, node: str):
        '''Creates a directory
        Args:
            dir_path (str): The name of the directory to be created
            node (str): The node in the cluster where the command is to be run
        '''

        cmd = f'mkdir {dir_path}'

        self.rlog(f"Running {cmd} on node {node}")
        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog("Successfully ran {cmd} on {node}")

    def ls(self, node: str, path: str):
        '''List the directory contents
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

        self.rlog("Successfully ran {cmd} on {node}")

    def run(self, node: str, cmd: str):
        '''Used for non-standard IO commands
        Args:
            node (str): The node in the cluster where the command is to be run
            cmd (str): The non-standard command which is to be run
        '''

        self.rlog(f"Running {cmd} on node {node}")
        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog("Successfully ran {cmd} on {node}")
