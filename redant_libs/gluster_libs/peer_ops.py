
from redant_libs.support_libs.rexe import Rexe

from redant_libs.redant_resources import Redant_Resources as RR

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
    try:

        RR.rlogger.info("Redant test framework started")
        cmd = 'gluster --xml peer probe %s' % server

        #TODO: remove the print 
        print("Running %s on node %s" % (cmd, node))

        RR.rlogger.info("Running %s on node %s" % (cmd,node))

        ret = R.execute_command(node=node, cmd=cmd)
        
        #TODO: remove the print
        pp.pprint(ret)

        RR.rlogger.info(ret)

        # For testing you can explicitly change the error_code to something other than 0 as shown below
        # ret['error_code'] = 2 
        if ret['error_code'] != 0:
            raise Exception(ret['msg']['opErrstr'])

    except Exception as error:
        RR.rlogger.error(error)
    return ret

def peer_detach(node, server, force=False):
    """Detach the specified server.

    Args:
        node (str): Node on which command has to be executed.
        server (str): Server to be detached from the cluster

    Kwargs:
        force (bool): option to detach peer. Defaults to False.

    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.
    """
    try:
        RR.rlogger.info("Peer detach initiated")

        #TODO: to be removed
        pp.pprint("Peer detach initiated")
        if force:
            cmd = "gluster --xml peer detach %s force --mode=script" % server
        else:
            cmd = "gluster --xml peer detach %s --mode=script" % server

        ret = R.execute_command(node, cmd)

        #TODO: to be removed
        pp.pprint(ret)
        
        RR.rlogger.info(ret)

        ret['error_code'] = 2
        if ret['error_code'] != 0:
            raise Exception(ret['msg']['opErrstr'])

    except Exception as error:
        RR.rlogger.error(error)

    return ret


def peer_status():
    """
    Checks the status of the peers
    """
    try:
        cmd = 'gluster --xml peer status'
        RR.rlogger.info("Running %s" % cmd)

        ret = R.execute_command(node='10.70.43.228', cmd=cmd)

        #TODO: remove the print
        pp.pprint(ret)
        RR.rlogger.info(ret)  

      
        if ret['error_code'] != 0:
            raise Exception(ret['msg']['opErrstr'])
    
    except Exception as error:
        RR.rlogger.error(error)

    return ret

def pool_list(node):
    """

    runs the command gluster pool list on `node`
    """
    try:
        cmd = 'gluster --xml pool list' 

        RR.rlogger.info("Running the command %s" % cmd)
        
        ret = R.execute_command(node=node, cmd=cmd)

        #TODO: remove the print
        pp.pprint(ret)

        RR.rlogger.info(ret)

 
        if ret['error_code'] != 0:
            raise Exception(ret['msg']['opErrstr'])
    
    except Exception as error:
        RR.rlogger.error(error)

    return ret

if __name__ == "__main__":
    
    
    R.establish_connection()

    """
    Add libraries to test the code 

    run the command: python3 redant_libs/peer_ops.py

    Test the libraries
    
    """

    peer_detach(node='10.70.43.228',server='10.70.43.101')
    peer_probe('10.70.43.101','10.70.43.228')
    peer_status()
    pool_list('10.70.43.101')