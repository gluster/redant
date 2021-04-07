"""
This file contains one class - io_ops which
holds API for running all the IO commands.
"""


class io_ops:
    """
    io_ops class provides API to handle 
    all the IO commands.
    """

    def execute_io_cmd(self, cmd: str, host: str = None):
    '''
    Used for all the IO commands

    Args:
        cmd (str): The IO command which is to be run
        host (str): The node in the cluster where the command is to be run
    '''

        self.rlog(f"Running {cmd} on node {host}")
        ret = self.execute_command(host, cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {host}")
