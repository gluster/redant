import sys

sys.path.append("./odinControl")

print(sys.path,"\n\n\n")

from rexe.rexe import Rexe

from redant_resources import Redant_Resources as RR

import pprint   # to print the output in a better way and hence more understandable

#TODO: test runner thread will provide the path. Using the below object temporarily
R = Rexe(conf_path="./Utilities/conf.yaml")

"""
For testing temporarily  

Utilities/conf.yaml

host_list: IPs
user: user
passwd: passwd

"""

# RR = Redant_Resources(log_file_path='./redant.log',log_file_level='D')

pp = pprint.PrettyPrinter(indent=4)


def peer_probe(server, node):
    """
    node: The node in the cluster where peer probe is to be run
    server: The server to probe
    """


    RR.rlogger.info("Redant test framework started")
    cmd = 'gluster --xml peer probe '+server

    #TODO: remove the print 
    print("Running ",cmd," on node ", node)

    RR.rlogger.info("Running "+cmd+" on node "+node)

    ret = R.execute_command(node=node, cmd=cmd)
    
    #TODO: remove the print
    pp.pprint(ret)

    RR.rlogger.info(ret)

    return ret

def peer_status():
    """
    Checks the status of the peers
    """

    cmd = 'gluster --xml peer status'
    RR.rlogger.info("Running "+cmd)

    ret = R.execute_command(node='10.70.43.228', cmd=cmd)
  
    #TODO: remove the print
    pp.pprint(ret)
    RR.rlogger.info(ret)  

    return ret

def pool_list(node):
    """

    runs the command gluster pool list on `node`
    """
    cmd = 'gluster --xml pool list' 

    RR.rlogger.info("Running the command "+cmd)
    
    ret = R.execute_command(node=node, cmd=cmd)

    #TODO: remove the print
    pp.pprint(ret)

    RR.rlogger.info(ret)

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