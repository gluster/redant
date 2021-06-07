"""
This file contains one class - PeerOps which
holds APIS related to peers which will be called
from the test case.
"""

import random
from time import sleep
import socket
from common.ops.abstract_ops import AbstractOps


class PeerOps(AbstractOps):
    """
    PeerOps class provides APIs to perform operations
    like probing and detaching the peers,checking the status
    and list of peers in the pool.
    """

    def peer_probe(self, server: str, node: str,
                   excep: bool = True) -> dict:
        """
        Adds a new peer to the cluster
        Args:
            server (str): The server to probe
            node (str): The node in the cluster where peer probe is to be run

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

        ret = self.execute_abstract_op_node(cmd, node, excep)

        return ret

    def peer_probe_servers(self, servers: list, node: str,
                           validate: bool = True,
                           time_delay: int = 10) -> bool:
        """
        Probe specified servers and validate whether probed servers
        are in cluster and connected state if validate is set to True.
        Args:
            servers (str|list): A server|List of servers to be peer probed.
            node (str): Node on which command has to be executed.
        Kwargs:
            validate (bool): True to validate if probed peer is in cluster and
                             connected state. False otherwise. Default is True
            time_delay (int): time delay before validating peer status.
                              Defaults to 10 seconds.
        Returns:
            bool: True on success and False on failure.
        """
        if not isinstance(servers, list):
            servers = [servers]
        else:
            servers = servers[:]

        if node in servers:
            servers.remove(node)

        # Get list of nodes from 'gluster pool list'
        nodes_in_pool_list = self.nodes_from_pool_list(node)
        if nodes_in_pool_list is None:
            self.logger.error("Unable to get nodes from gluster pool list. "
                              "Failing peer probe.")
            return False

        for server in servers:
            if server not in nodes_in_pool_list:
                ret = self.peer_probe(server, node, False)
                if 'output' not in ret['msg']:
                    return False
                if (ret['error_code'] != 0
                        or ret['msg']['output'] != 'success'
                        or ret['msg']['opRet'] != '0'):
                    self.logger.error("Failed to peer probe the node"
                                      f" {server}")
                    return False
                else:
                    self.logger.info("Successfully peer probed the node"
                                     f" {server}")

        # Validating whether peer is in connected state after peer probe
        if validate:
            sleep(time_delay)
            if not self.is_peer_connected(servers, node):
                self.logger.error("Validation after peer probe failed.")
                return False
            else:
                self.logger.info("Validation after peer probe is successful.")

        return True

    def peer_detach(self, server: str, node: str, force: bool = False,
                    excep: bool = True) -> dict:
        """
        Detach the specified server.
        Args:
            server (str): Server to be detached from the cluster
            node (str): Node on which command has to be executed.
            force (bool): if set to true will execute the peer
                          detach command with force option.
            excep (bool): exception flag to bypass the exception if the
                          peer detach command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True

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

        ret = self.execute_abstract_op_node(cmd, node, excep)

        return ret

    def peer_detach_servers(self, servers: list, node: str,
                            force: bool = False, validate: bool = True,
                            time_delay: int = 10) -> bool:
        """
        Detach peers and validate status of peer if validate is set to True.

        Args:
            servers (str|list): A server|List of servers to be detached.
            node (str): Node on which command has to be executed.

        Kwargs:
            force (bool): option to detach peer.
                          Defaults to False.
            validate (bool): True if status of the peer needs to be validated,
                             False otherwise. Defaults to True.
            time_delay (int): time delay before executing validating peer.
                              status. Defaults to 10 seconds.

        Returns:
            bool: True on success and False on failure.
        """
        if not isinstance(servers, list):
            servers = [servers]
        else:
            servers = servers[:]

        if node in servers:
            servers.remove(node)

        for server in servers:
            ret = self.peer_detach(server, node, force, False)
            if (ret['error_code'] != 0
                    or ret['msg']['output'] != 'success'
                    or ret['msg']['opRet'] != '0'):
                self.logger.error(f"Failed to detach the node {server}")
                return False

        # Validating whether peer detach is successful
        if validate:
            sleep(time_delay)
            nodes_in_pool = self.nodes_from_pool_list(node)
            rc = True
            for server in servers:
                if server in nodes_in_pool:
                    self.logger.error(f"Peer {server} still in pool")
                    rc = False
            if not rc:
                self.logger.error("Validation after peer detach failed.")
            else:
                self.logger.info("Validation after peer detach is successful")

        return True

    def get_peer_status(self, node: str) -> list:
        """
        Checks the status of the peers
        Args:
            node (str): Node on which command has to be executed.

        Returns:
            'peer'(list|dict): If single peer is present then dict is returned
                               If multiple peers are present then list is
                               returned
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
            None on failure
        """
        pool_list_data = self.get_pool_list(node)

        if pool_list_data is None:
            self.logger.error("Unable to get Nodes")
            return None

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
                return self.convert_hosts_to_ip(nodes, node)
        except Exception:
            pass
        for item in pool_list_data:
            nodes.append(item['hostname'])
        return self.convert_hosts_to_ip(nodes, node)

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
        Returns:
            list : list of converted IPs
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

    def is_peer_connected(self, servers: list, node: str) -> bool:
        """
        Checks whether specified peers are in cluster and 'Connected' state.
        Args:
            servers (str|list): A server|List of servers to be validated.
            node (str): Node on which peer status has to be executed.
        Returns
            bool : True on success (peer in cluster and connected), False on
                   failure.
        """
        if not isinstance(servers, list):
            servers = [servers]
        else:
            servers = servers[:]

        for index, server in enumerate(servers):
            servers[index] = socket.gethostbyname(server)

        if node in servers:
            servers.remove(node)

        peer_status_list = self.get_peer_status(node)
        if peer_status_list is None:
            return False
        elif not isinstance(peer_status_list, list):
            peer_status_list = [peer_status_list]

        is_connected = True
        for peer_stat in peer_status_list:
            if (socket.gethostbyname(peer_stat['hostname']) in servers
                and (peer_stat['stateStr'] != "Peer in Cluster"
                     or peer_stat['state'] != '3'
                     or peer_stat['connected'] != '1')):
                self.logger.error(f"Peer '{peer_stat['hostname']}' "
                                  f"not in connected state")
                is_connected = False

        if not is_connected:
            return False

        # check which server in servers is not part of the pool itself
        peer_ips = [socket.gethostbyname(peer_stat['hostname']) for
                    peer_stat in peer_status_list]

        if not set(servers).issubset(peer_ips):
            servers_not_in_pool = list(set(servers).difference(peer_ips))
            for index, server in enumerate(servers_not_in_pool):
                if server not in servers:
                    servers_not_in_pool[index] = (socket.
                                                  gethostbyaddr(server)[0])
            self.logger.error(f"Servers: {servers_not_in_pool} not "
                              "yet added to the pool.")
            return False
        return is_connected

    def wait_for_peers_to_connect(self, servers: list, node: str,
                                  wait_timeout: int = 10) -> bool:
        """
        Checks nodes are peer connected with timeout.
        Args:
            servers (str|list): A server|List of server hosts on which peer
                                status has to be checked.
            node: node on which cmd has to be executed.
            wait_timeout: timeout to retry connected status check in node.
        Returns:
            bool : True if all the peers are connected.
                   False otherwise.
        """
        if not isinstance(servers, list):
            servers = [servers]

        count = 0
        while count <= wait_timeout:
            ret = self.is_peer_connected(servers, node)
            if ret:
                return True
            sleep(1)
            count += 1
        return False

    def validate_peers_are_connected(self, server_list: list,
                                     node: str = None) -> bool:
        """
        Validate whether each server in the cluster is connected to
        all other servers in cluster.

        Args:
            server_list (list) : List of servers
            node (str) : node on which caommand is to be executed

        Returns (bool): True if all peers are in connected
                        state with other peers.
                        False otherwise.
        """
        # if the setup has single node cluster
        # then by-pass this validation
        if not isinstance(server_list, list):
            server_list = [server_list]

        if len(server_list) == 1:
            return True

        # validate if peer is connected from all
        # the servers
        self.logger.info(f"Validating if {server_list} are connnected in"
                         f" the cluster")

        for server in server_list:
            self.logger.info(f"Is peer connected {server}->{server_list}")
            ret = self.is_peer_connected(server_list, server)

            if not ret:
                self.logger.error(f"Servers are not in connected state"
                                  f" from {server}")
                return False

        self.logger.info("Successfully validated. All the servers"
                         " in the cluster are connected")
        if node is None:
            node = random.choice(server_list)
        self.get_peer_status(node)
        return True

    def wait_till_all_peers_connected(self, server_list: list,
                                      timeout=100) -> bool:
        """
        Wait till all said peers are connected.

        Args:
            server_list (str)
        Returns:
            bool: True if everything is perfect. Else False
        """
        iter_v = 0
        while iter_v < timeout:
            ret = self.validate_peers_are_connected(server_list)
            if ret:
                return True
            sleep(1)
            iter_v += 1

        return False
