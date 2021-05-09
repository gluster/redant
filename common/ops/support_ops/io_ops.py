"""
This file contains one class - IoOps which
holds API for running all the IO commands.
"""
from common.ops.abstract_ops import AbstractOps


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

    def create_file(self, path: str, filename: str, node: str):
        """
        Creates a file in the specified specified path
        """
        cmd = f"touch {path}/{filename}"
        self.execute_abstract_op_node(cmd, node)

    def create_dir(self, path: str, dirname: str, node: str):
        """
        Creates a directory in the specified path
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
