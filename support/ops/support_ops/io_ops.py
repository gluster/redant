"""
This file contains one class - IoOps which
holds API for running all the IO commands.
"""
from support.ops.abstract_ops import AbstractOps


class IoOps(AbstractOps):
    """
    IoOps class provides API to handle
    all the IO commands.
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
