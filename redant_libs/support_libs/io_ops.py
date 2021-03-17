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

    def touch(self, file_name: str, node: str):
        """Creates a regular empty file
        Args:
            file_name (str): The name of the file to be created
            node (str): The node in the cluster where the command is to be run
        """

        cmd = "touch {}".format(file_name)

        self.rlog(f"Running {cmd} on node {node}")
        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog("Successfully ran {cmd} on {node}")

    def mkdir(self, dir_name: str, node: str):
        '''Creates a directory
        Args:
            dir_name (str): The name of the directory to be created
            node (str): The node in the cluster where the command is to be run
        '''

        cmd = f'mkdir -p /{dir_name}'

        self.rlog(f"Running {cmd} on node {node}")
        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog("Successfully ran {cmd} on {node}")

    def ls(self, node: str):
        '''List the directory contents
        Args:
            node (str): The node in the cluster where the command is to be run
        '''

        cmd = 'ls'

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
