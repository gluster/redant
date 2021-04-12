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
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
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
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
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
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
        """

        cmd = 'gluster --xml peer status'

        self.logger.info(f"Running {cmd} on node {node}")

        ret = self.execute_command(node, cmd)

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
        ret = self.execute_command(node, cmd)
        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        peer_list = []
        
        peers = ret['msg']['peerStatus']['peer']
        if not isinstance(peers,list):
            peers = [peers]
            
        for peer in peers:
            if peer['connected']=='1':
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
        ret = self.execute_command(node, cmd)

        if ret['error_code'] != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

        peer_dict = ret['msg']

        pool_list = peer_dict['peerStatus']['peer']

        return pool_list
    
    def create_cluster(self, nodes: list) -> bool:
        """
        Creates a cluster by probing all the nodes in the list.
        Args:
            node (list): All the nodes which form the cluster.
        Returns:
            True: If nodes are in cluster or number of nodes are 0 or 1.
            False: If cluster cannot be created.
        """
        
        length = len(nodes)
        if length==0 or length==1:
            return True
        
        peer_list = []
        
        count = 0
        
        for node in nodes:
            pool_list = self.pool_list(node)
            if count==0:
                peer_list = pool_list
            else:
                if len(peer_list)==len(pool_list):
                    for peer in peer_list:
                        if peer not in pool_list and len(peer_list)!=1:
                            break
                else:
                    break
            count += 1
            
        if count==len(nodes):
            if len(peer_list)==1:
                
                node = nodes[0]
                self.logger.info("Creating cluster")
                for server in nodes:
                    self.peer_probe(server,node)
                self.logger.info("Cluster created")
            return True
        else:
            return False
