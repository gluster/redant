import os
from rexe.rexe import Rexe

from redant_resources import (
    Redant_Resources,
    logger
)

import pprint   # to print the output in a better way and hence more understandable

R = Rexe(conf_path="./Utilities/conf.yaml")

"""
For testing temporarily  

Utilities/conf.yaml

host_list: IPs
user: user
passwd: passwd

"""

RR = Redant_Resources(log_file_path='./redant.log',log_file_level='D')

pp = pprint.PrettyPrinter(indent=4)


def peer_probe(server, node):
    """
    node: The node in the cluster where peer probe is to be run
    server: The server to probe
    """


    logger.info("Redant test framework started")
    cmd = 'gluster peer probe '+server

    #TODO: remove the print 
    print("Running ",cmd," on node ", node)

    logger.info("Running "+cmd+" on node "+node)

    ret = R.execute_command(node=node, cmd=cmd)
    
    #TODO: remove the print
    pp.pprint(ret)

    logger.info(ret)

    return ret

def peer_status():
    """
    Checks the status of the peers
    """

    cmd = 'gluster peer status --xml'
    logger.info("Running "+cmd)

    ret = R.execute_command(node='10.70.43.228', cmd=cmd)
  
    #TODO: remove the print
    pp.pprint(ret)
    

    return ret

def pool_list(node):
    """

    runs the command gluster pool list on `node`
    """
    cmd = 'gluster pool list'

    logger.info("Running the command "+cmd)
    
    ret = R.execute_command(node=node, cmd=cmd)

    #TODO: remove the print
    pp.pprint(ret)

    logger.info(ret)

    return ret

if __name__ == "__main__":
    
    
    R.establish_connection()

    """
    Add libraries to test the code 

    run the command: python3 redant_libs/peer_ops.py

    Test the libraries
    
    """

    peer_probe('10.70.43.101','10.70.43.228')
    peer_status()
    pool_list('10.70.43.101')