import os
from rexe.rexe import Rexe
R = Rexe(conf_path="./Utilities/conf.yaml")

def peer_probe(server, node):
    """
    node: The node in the cluster where peer probe is to be run
    server: The server to probe
    """


    cmd = 'gluster peer probe '+server
    print("Running ",cmd," on node ", node)
    
    ret = R.execute_command(node=node, cmd=cmd)
    print("Command running properly!")
    print(ret)

def peer_status():
    """
    Checks the status of the peers
    """

    cmd = 'gluster peer status'
    ret = R.execute_command(node='10.70.43.228', cmd=cmd)
    print(ret)
    return ret


if __name__ == "__main__":
    R.establish_connection()
    peer_probe('10.70.43.101','10.70.43.228')
    peer_status()