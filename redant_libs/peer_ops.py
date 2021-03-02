

def peer_probe(servers, nodes):
    """
    nodes: The nodes in the cluster
    servers: The list of servers that need to run the peer probe
    """
    for node in nodes:

        """
            It will probe all the servers in the list
        """

        cmd = 'gluster peer probe '+node
        print(cmd)
        print(type(cmd))

def peer_status():
    pass

peer_probe(['nodea', 'nodeb'],['servera','serverb'])