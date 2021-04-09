"""
This file contains one class - peer_ops which
holds APIS related to peers which will be called
from the test case.
"""


class peer_ops:
    """
    peer_ops class provides APIs to perform operations
    like adding and deleting the peers,checking the status
    and list of peers in the pool.
    """

    def peer_probe(self, server: str, node: str):
        """
        Adds a new peer to the cluster
        Args:
            node (str): The node in the cluster where peer probe is to be run
            server (str): The server to probe

        Returns:
            tuple: Tuple containing three elements (ret, out, err).
                The first element 'ret' is of type 'int' and
                is the return value
                of command execution.

                The second element 'out' is of type 'str'
                and is the stdout value
                of the command execution.

                The third element 'err' is of type 'str'
                and is the stderr value
                of the command execution.
        """

        cmd = f'gluster --xml peer probe {server}'

        self.logger.info(f"Running {cmd} on node {node}")
        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")
        return ret

    def peer_detach(self, node: str, server: str, force: bool = False):
        """
        Detach the specified server.
        Args:
            node (str): Node on which command has to be executed.
            server (str): Server to be detached from the cluster

        Kwargs:
            force (bool): option to detach peer. Defaults to False.

        Returns:
            tuple: Tuple containing three elements (ret, out, err).
                The first element 'ret' is of type 'int' and
                is the return value
                of command execution.

                The second element 'out' is of type 'str'
                and is the stdout value
                of the command execution.

                The third element 'err' is of type 'str'
                and is the stderr value
                of the command execution.
        """

        if force:
            cmd = f"gluster --xml peer detach {server} force --mode=script"
        else:
            cmd = f"gluster --xml peer detach {server} --mode=script"
        self.logger.info(f"Running {cmd} on node {node}")
        ret = self.execute_command(node, cmd)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")
        return ret

    def peer_status(self, node: str):
        """
        Checks the status of the peers
        Args:
            node (str): Node on which command has to be executed.

        Returns:
            tuple: Tuple containing three elements (ret, out, err).
                The first element 'ret' is of type 'int' and
                is the return value
                of command execution.

                The second element 'out' is of type 'str'
                and is the stdout value
                of the command execution.

                The third element 'err' is of type 'str'
                and is the stderr value
                of the command execution.
        """

        cmd = 'gluster --xml peer status'

        self.logger.info(f"Running {cmd} on node {node}")

        ret = self.execute_command(node, cmd)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")
        return ret

    def pool_list(self, node: str):
        """
        Runs the command gluster pool list on `node`
        Args:
            node (str): Node on which command has to be executed.

        Returns:
            tuple: Tuple containing three elements (ret, out, err).
                The first element 'ret' is of type 'int' and
                is the return value
                of command execution.

                The second element 'out' is of type 'str'
                and is the stdout value
                of the command execution.

                The third element 'err' is of type 'str'
                and is the stderr value
                of the command execution.
        """

        cmd = 'gluster --xml pool list'
        self.logger.info(f"Running {cmd} on node {node}")
        ret = self.execute_command(node, cmd)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")
        return ret

    def nodes_from_pool_list(self, node: str):
        """
        Return list of nodes from the 'gluster pool list'.

        Args:
            node (str): Node on which command has to be executed.

        Returns:
            list: List of nodes in pool on Success, Empty list on failure.
        """
        pool_list_data = self.get_pool_list(node)

        if pool_list_data is None:
            self.logger.info("Unable to get Nodes")

        nodes = []
        for item in pool_list_data:
            nodes.append(item['hostname'])
        return nodes

    def get_pool_list(self, node: str):
        """
        Parse the output of 'gluster pool list' command.

        Args:
            node (str): Node on which command has to be executed.

        Returns:
            list : list of dicts on success.
        """

        cmd = 'gluster pool list --xml'

        self.logger.info(f"Running {cmd} on node {node}")
        ret = self.execute_command(node, cmd)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

        peer_dict = ret['msg']

        pool_list = peer_dict['peerStatus']['peer']

        return pool_list
