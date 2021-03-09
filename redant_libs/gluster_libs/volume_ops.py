from rexe import Rexe
from redant_resources import Redant_Resources as RR

#TODO: this is for testing. When test runner will be ready it will be removed.
R = Rexe(conf_path="./example/conf.yaml")


def volume_create(mnode,volname,bricks_list,force=False, **kwargs):
    """Create the gluster volume with specified configuration
    Args:
        mnode(str): server on which command has to be executed
        volname(str): volume name that has to be created
        bricks_list (list): List of bricks to use for creating volume.

    Kwargs:
        force (bool): If this option is set to True, then create volume
            will get executed with force option. If it is set to False,
            then create volume will get executed without force option
        **kwargs
            The keys, values in kwargs are:
                - replica_count : (int)|None
                - arbiter_count : (int)|None
                - stripe_count : (int)|None
                - disperse_count : (int)|None
                - disperse_data_count : (int)|None
                - redundancy_count : (int)|None
                - transport_type : tcp|rdma|tcp,rdma|None
                - ...
    Returns:
        a dictionary generated from the stdout xml output.
    """
    replica_count = arbiter_count = stripe_count = None
    disperse_count = disperse_data_count = redundancy_count = None
    transport_type = None

    if 'replica_count' in kwargs:
        replica_count = int(kwargs['replica_count'])

    if 'arbiter_count' in kwargs:
        arbiter_count = int(kwargs['arbiter_count'])

    if 'stripe_count' in kwargs:
        stripe_count = int(kwargs['stripe_count'])

    if 'disperse_count' in kwargs:
        disperse_count = int(kwargs['disperse_count'])

    if 'disperse_data_count' in kwargs:
        disperse_data_count = int(kwargs['disperse_data_count'])

    if 'redundancy_count' in kwargs:
        redundancy_count = int(kwargs['redundancy_count'])

    if 'transport_type' in kwargs:
        transport_type = kwargs['transport_type']

    replica = arbiter = stripe = disperse = disperse_data = redundancy = ''
    transport = ''
    if replica_count is not None:
        replica = "replica %d" % replica_count

    if arbiter_count is not None:
        arbiter = "arbiter %d" % arbiter_count

    if stripe_count is not None:
        stripe = "stripe %d" % stripe_count

    if disperse_count is not None:
        disperse = "disperse %d" % disperse_count

    if disperse_data_count is not None:
        disperse_data = "disperse-data %d" % disperse_data_count

    if redundancy_count is not None:
        redundancy = "redundancy %d" % redundancy_count

    if transport_type is not None:
        transport = "transport %s" % transport_type

    cmd = ("gluster volume create %s %s %s %s %s %s %s %s %s --xml "
           "--mode=script" % (volname, replica, arbiter, stripe,
                              disperse, disperse_data, redundancy,
                              transport, ' '.join(bricks_list)))
    
    RR.rlogger.info("Volume creation started")
    
    if force:
        cmd = cmd + " force"

    ret =  R.execute_command(node=mnode,cmd=cmd)
    
    #TODO: to be removed later
    print(ret)
    
    RR.rlogger.info(ret)
    
    return ret

def volume_start(mnode,volname,force=False):
    """Starts the gluster volume
    Args:
        mnode (str): Node on which cmd has to be executed.
        volname (str): volume name
    Kwargs:
        force (bool): If this option is set to True, then start volume
            will get executed with force option. If it is set to False,
            then start volume will get executed without force option
    Returns:
        a dictionary generated from the stdout xml output.
    """

    RR.rlogger.info("Starting gluster volume")

    if force:
        cmd = "gluster volume start %s force --mode=script --xml" % volname
    else:
        cmd = "gluster volume start %s --mode=script --xml" %volname

    ret = R.execute_command(node=mnode,cmd=cmd)

    #TODO: to be removed later
    print(ret)

    RR.rlogger.info(ret)
    return ret

def volume_stop(mnode,volname,force=False):
    """Starts the gluster volume
    Args:
        mnode (str): Node on which cmd has to be executed.
        volname (str): volume name
    Kwargs:
        force (bool): If this option is set to True, then start volume
            will get executed with force option. If it is set to False,
            then start volume will get executed without force option
    Returns:
        a dictionary generated from the stdout xml output.
    """

    RR.rlogger.info("Volume Stop Command initiated")

    if force:
        cmd = "gluster volume stop %s force --mode=script --xml" % volname
    else:
        cmd = "gluster volume stop %s --mode=script --xml" %volname

    ret = R.execute_command(node=mnode,cmd=cmd)
    
    #TODO: to be removed later
    print(ret)

    RR.rlogger.info(ret)
    
    return ret

def volume_delete(mnode,volname):
    """Deletes the gluster volume if given volume exists in
       gluster and deletes the directories in the bricks
       associated with the given volume
    Args:
        mnode (str): Node on which cmd has to be executed.
        volname (str): volume name
    Returns:
        a dictionary generated from the stdout xml output.
    """

    RR.rlogger.info("Volume Delete Command initiated")
    cmd = 'gluster volume delete %s --mode=script --xml' % volname
    ret = R.execute_command(node=mnode,cmd=cmd)
    RR.rlogger.info(ret)
    return ret
    
    

def volume_info(mnode,volname='all'):
    """Gives volume information
    Args:
        node (str): Node on which cmd has to be executed.
        volname (str): volume name
    Returns:
        a dictionary with volume information.
    """

    RR.rlogger.info("Volume Delete Command initiated")
    cmd = 'gluster volume info %s --xml' % volname
    ret = R.execute_command(node=mnode,cmd=cmd)
    volume_info = ret['msg']

    RR.rlogger.info(ret)
    ret_val = volume_info['volInfo']['volumes']['volume']

    return ret_val




if __name__ == "__main__":
    R.establish_connection()
    mnode = "10.70.43.63"
    bricks_list = ["gluster2:/gluster/brick1"]
    #volume_create(mnode,"test-vol",bricks_list,force=True)
    #volume_start(mnode,"test-vol")
    #volume_stop(mnode,"test-vol")
    #volume_info(mnode)
    #volume_delete(mnode,"test-vol")
