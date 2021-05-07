"""
This file contains one class - PeerOps which
holds APIS related to peers which will be called
from the test case.
"""

import random
from time import sleep
import socket
import re
from time import sleep
from common.ops.abstract_ops import AbstractOps


class PeerOps(AbstractOps):
    """
    PeerOps class provides APIs to perform operations
    like adding and deleting the peers,checking the status
    and list of peers in the pool.
    """

    def peer_probe(self, server: str, node: str) -> dict:
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

        ret = self.execute_abstract_op_node(cmd, node)

        ret_probe = self.wait_for_peers_to_connect(node, server)

        if not ret_probe:
            raise Exception(f"Peer {node} could not be connected.")

        return ret

    def peer_detach(self, server: str, node: str, force: bool = False) -> dict:
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

        ret = self.execute_abstract_op_node(cmd, node)

        return ret

    def get_peer_status(self, node: str) -> list:
        """
        Checks the status of the peers
        Args:
            node (str): Node on which command has to be executed.

        Returns:
            'peer'(list|dict): If single peer is present then dict is returned
                                If multiple peers are present then list is returned
            {
                'uuid': '504fdf87-805a-4e8f-a266-b2f45d76958a',
                'hostname': 'dhcp42-209.lab.eng.blr.redhat.com',
                'hostnames': {
                                'hostname': [
                                                'dhcp1.1.lab.eng.blr.redhat.com',
                                                '1.1.1.1'
                                            ]
                            },
                'connected': '1',
                'state': '3',
                'stateStr': 'Peer in Cluster'
            }

        """

        cmd = 'gluster --xml peer status'

        ret = self.execute_abstract_op_node(cmd, node)

        if ret['msg']['peerStatus'] is None:
            return None

        return ret['msg']['peerStatus']['peer']

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
        # WHY?
        # The pool_list_data is a simple dict of the form
        # {'uuid' : 'val', 'hostname' : 'val',...} when the node isn't
        # part of any cluster.
        # And a list of dictionaries when multiple nodes are present. This
        # causes an issue in obtaining the hostname in a generic manner, hence
        # this if statement which checks for hostname in keys BUT!! this will
        # cause an exception if the said value contains lists of dict, hence
        # the try-except block.
        # If anyone were to come across a better syntax, do change this
        # monstrosity.
        try:
            if 'hostname' in pool_list_data.keys():
                nodes.append(pool_list_data['hostname'])
                return nodes
        except Exception:
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

        ret = self.execute_abstract_op_node(cmd, node)
        peer_dict = ret['msg']
        pool_list = peer_dict['peerStatus']['peer']

        return pool_list

    def convert_hosts_to_ip(self, node_list: list, node: str) -> list:
        """
        Redant framework works with IP addresses ( especially rexe )
        hence it makes sense to have a function to handle the conversion
        a node_list containing hostnames to ip addresses and if there's
        a localhost term, that is replaced by the node value.
        Args:
            node_list (list): List of nodes obtained wherein the node can
                              be represented by ip or hostname.
            node (str): The node which is represented by localhost. Has to
                        be replaced by corresponding IP.
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
        Returns:
            bool: Representing whether the cluster created failed
            or passed.
        """
        if len(node_list) in [0, 1]:
            return False
        desired_cluster_size = len(node_list)
        main_cluster = self.convert_hosts_to_ip(self.nodes_from_pool_list(
                                                node_list[0]), node_list[0])
        main_cluster_size = len(main_cluster)
        if main_cluster_size == desired_cluster_size:
            return True
        for node in node_list:
            temp_cluster = self.convert_hosts_to_ip(self.nodes_from_pool_list(
                                                    node), node)
            self.delete_cluster(temp_cluster)
        node = random.choice(node_list)
        for nd in node_list:
            if nd == node:
                continue
            self.peer_probe(nd, node)
        while len(self.nodes_from_pool_list(node_list[0])) != \
                desired_cluster_size:
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
        node = random.choice(node_list)
        for nd in node_list:
            if nd == node:
                continue
            self.peer_detach(nd, node)

    def is_peer_connected(self, node: str, servers: list) -> bool:
        """
        Checks whether specified peers are in cluster and 'Connected' state.
        Args:
            node (str): Node from which peer probe has to be executed.
            servers (str|list): A server|List of servers to be validated.
        Returns
            bool : True on success (peer in cluster and connected), False on
                failure.
        """
        if not isinstance(servers, list):
            servers = [servers]

        if node in servers:
            servers.remove(node)

        peer_status_list = self.get_peer_status(node)
        if peer_status_list is None:
            return False
        elif not isinstance(peer_status_list, list):
            peer_status_list = [peer_status_list]

        # Convert all hostnames to ip's
        server_ips = []
        for server in servers:
            server_ips.append(socket.gethostbyname(server))

        is_connected = True
        for peer_stat in peer_status_list:
            if socket.gethostbyname(peer_stat['hostname']) in server_ips:
                if (re.match(r'([0-9a-f]{8})(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',
                             peer_stat['uuid'], re.I) is None):
                    self.logger.error(
                        f"Invalid UUID for the node '{peer_stat['hostname']}'")
                    is_connected = False
                if (peer_stat['stateStr'] != "Peer in Cluster" or
                        peer_stat['connected'] != '1'):
                    self.logger.error(
                        f"Peer '{peer_stat['hostname']}' not in connected state")
                    is_connected = False

        if not is_connected:
            return False

        return True

    def wait_for_peers_to_connect(self, node: str, servers: list, wait_timeout: int = 10) -> bool:
        """
        Checks nodes are peer connected with timeout.
        Args:
            node: node on which cmd has to be executed.
            servers (str|list): A server|List of server hosts on which peer
                status has to be checked.
            wait_timeout: timeout to retry connected status check in node.
        Returns:
            bool : True if all the peers are connected.
                   False otherwise.
        """
        if not isinstance(servers, list):
            servers = [servers]

        count = 0
        while count <= wait_timeout:
            ret = self.is_peer_connected(node, servers)
            if ret:
                return True
            sleep(1)
            count += 1
        self.logger.error(f"Peers are not in connected state: {servers}")
        return False
