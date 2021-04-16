"""
This file contains one class - PeerOps which
holds APIS related to peers which will be called
from the test case.
"""
import socket

class PeerOps:
    """
    PeerOps class provides APIs to perform operations
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
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """

        cmd = f'gluster --xml peer probe {server}'

        self.logger.info(f"Running {cmd} on node {node}")
        ret = self.execute_command(cmd, node)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

        return ret

    def peer_detach(self, server: str, node: str, force: bool = False):
        """
        Detach the specified server.
        Args:
            node (str): Node on which command has to be executed.
            server (str): Server to be detached from the cluster

        Kwargs:
            force (bool): option to detach peer. Defaults to False.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        if force:
            cmd = f"gluster --xml peer detach {server} force --mode=script"
        else:
            cmd = f"gluster --xml peer detach {server} --mode=script"
        self.logger.info(f"Running {cmd} on node {node}")
        ret = self.execute_command(cmd, node)

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
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        cmd = 'gluster --xml peer status'

        self.logger.info(f"Running {cmd} on node {node}")

        ret = self.execute_command(cmd, node)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

        return ret

    def pool_list(self, node: str) -> list:
        """
        Runs the command gluster pool list on `node`
        Args:
            node (str): Node on which command has to be executed.

        Returns:
            list : gives list of all the UUID's of all the connected peers
        """

        cmd = 'gluster --xml pool list'
        self.logger.info(f"Running {cmd} on node {node}")
        ret = self.execute_command(cmd, node)
        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        peer_list = []

        peers = ret['msg']['peerStatus']['peer']
        if not isinstance(peers, list):
            peers = [peers]

        for peer in peers:
            if peer['connected'] == '1':
                peer_list.append(peer['uuid'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

        return peer_list

    def nodes_from_pool_list(self, node: str) -> list:
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
        """
        WHY?
        The pool_list_data is a simple dict of the form
        {'uuid' : 'val', 'hostname' : 'val',...} when the node isn't
        part of any cluster.
        And a list of dictionaries when multiple nodes are present. This
        causes an issue in obtaining the hostname in a generic manner, hence
        this if statement which checks for hostname in keys BUT!! this will
        cause an exception if the said value contains lists of dict, hence
        the try-except block.
        If anyone were to come across a better syntax, do change this
        monstrosity.
        """
        try:
            if 'hostname' in pool_list_data.keys():
                nodes.append(pool_list_data['hostname'])
                return nodes
        except:
            pass
        for item in pool_list_data:
            nodes.append(item['hostname'])
        return nodes

    def get_pool_list(self, node: str) -> list:
        """
        Parse the output of 'gluster pool list' command.

        Args:
            node (str): Node on which command has to be executed.

        Returns:
            list : list of dicts on success.
        """

        cmd = 'gluster pool list --xml'

        self.logger.info(f"Running {cmd} on node {node}")
        ret = self.execute_command(cmd, node)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

        peer_dict = ret['msg']

        pool_list = peer_dict['peerStatus']['peer']
        return pool_list

    def _add_orphan_nodes_to_cluster(self, cluster_nodes: list,
                                     orphan_nodes: list):
        """
        This function is useful for adding orphan nodes to an existing cluster
        one by one.
        Args:
            cluster_nodes (list): The list of nodes which are part of existing
                                  cluster.
            orphan_nodes (list): The list of nodes which aren't part of any
                                 cluster and need to be added to the existing
                                 cluster.
        """
        # Select any node randomly from the list for peer probing.
        import random
        node = random.choice(cluster_nodes)
        for nd in orphan_nodes:
            self.peer_probe(nd, node)

    def convert_hosts_to_ip(self, node_list: list, node: str):
        """
        Redant framework works with IP addresses ( especially rexe )
        hence it makes sense to have a function to handle the conversion
        a node_list containing hostnames to ip addresses and if there's
        a localhost term, that is replaced by the node value.
        """
        if 'localhost' in node_list:
            node_list.remove('localhost')
            node_list.append(node) 
        for value in node_list:
            if not value.replace('.', '').isnumeric():
                ip_val = socket.gethostbyname(value)
                node_list.remove(value)
                node_list.append(ip_val)
        return node_list

    def create_cluster(self, node_list: list) -> bool:
        """
        Creates a cluster out of given set of nodes irrespective
        of their existing cluster configurations.
        Args:
            node_list (list): All nodes which are to be part of the cluster.
        """
        if len(node_list) in [0, 1]:
            return False
        desired_cluster_size = len(node_list)
        main_cluster = self.convert_hosts_to_ip(self.nodes_from_pool_list(\
                                                node_list[0]), node_list[0])
        main_cluster_size = len(main_cluster)
        for node in node_list[1:]:
            if main_cluster_size == desired_cluster_size:
                return True
            elif node in main_cluster:
                continue
            temp_cluster = self.convert_hosts_to_ip(self.nodes_from_pool_list(\
                                                    node), node)
            if len(temp_cluster) > main_cluster_size:
                temp_cluster, main_cluster = main_cluster, temp_cluster
                main_cluster_size = len(temp_cluster)
            self.delete_cluster(temp_cluster)
            self._add_orphan_nodes_to_cluster(main_cluster, temp_cluster)
            main_cluster = main_cluster + temp_cluster
            main_cluster_size = len(main_cluster)
        from time import sleep
        while len(self.nodes_from_pool_list(node_list[0])) != \
              main_cluster_size:
            sleep(1)
        return True

    def delete_cluster(self, node_list: list):
        """
        Clusters have to be broken down to make way for new ones :p
        Args:
            node_list (list) : List of nodes which are part of a cluster
                               which is to be broken up.
        """
        # Select any node randomly from the list for peer detaching.
        if len(node_list) in [0, 1]:
            return
        import random
        node = random.choice(node_list)
        temp_node_list = node_list.remove(node)
        for nd in temp_node_list:
            self.peer_detach(nd, node)
