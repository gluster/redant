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

        self.rlog(f"Running {cmd} on node {node}")
        ret = self.execute_command(node=node, cmd=cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")
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
        self.rlog(f"Running {cmd} on node {node}")
        ret = self.execute_command(node, cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")
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

        self.rlog(f"Running {cmd} on node {node}")

        ret = self.execute_command(node, cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")
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
        self.rlog(f"Running {cmd} on node {node}")
        ret = self.execute_command(node, cmd)

        if ret['error_code'] != 0:
            self.rlog(ret['msg']['opErrstr'], 'E')
            raise Exception(ret['msg']['opErrstr'])

        self.rlog(f"Successfully ran {cmd} on {node}")
        return ret
