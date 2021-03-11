import sys
import os

from redant_libs.support_libs.rexe import Rexe

from redant_libs.redant_resources import Redant_Resources as RR

import pprint   # to print the output in a better way and hence more understandable

#TODO: test runner thread will provide the path. Using the below object temporarily
R = Rexe(conf_path="./Utilities/conf.yaml")

pp = pprint.PrettyPrinter(indent=4)


""" def volume_mount(mnode , volname , dir,force=False):
    RR.rlogger.info("Volume Mount Command initiated")

    if force:
        cmd = "mount -t --force glusterfs "+mnode+":/"+volname+" /"+dir
    else:
        cmd = "mount -t glusterfs "+mnode+":/"+volname+" /"+dir

    ret = R.execute_command(node="10.70.43.63",cmd=cmd)
    
    #TODO: to be removed later
    print(ret)

    RR.rlogger.info(ret)
    
    return ret """

def touch(self, file_name):

    try:
        """Creates a regular empty file"""
        RR.rlogger.info("Creating File")

    
        cmd = "touch {}".format(file_name)

        ret = R.execute_command(node="192.168.122.161", cmd=cmd)

        #TODO: to be removed
        pp.pprint(ret)
    
        RR.rlogger.info(ret)

        if ret['error_code'] != 0:
            raise Exception(ret['msg'])
    
    except Exception as e:
        RR.rlogger.error(e)

    
    return ret


def mkdir(self,dir_name):

    try:
        RR.rlogger.info("Creating Directory")
    
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        cmd = 'mkdir -p /'+ ROOT_DIR + '/'+dir_name
      

        ret = R.execute_command(node="192.168.122.161", cmd=cmd)

        #TODO: to be removed
        pp.pprint(ret)
    
        RR.rlogger.info(ret)

        if ret['error_code'] != 0:
            raise Exception(ret['msg'])
    
    except Exception as e:
        RR.rlogger.error(e)

    
    return ret


def ls():

    try:
        RR.rlogger.info("List the files on root directory")

        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    
        cmd = 'ls /'+ ROOT_DIR

        ret = R.execute_command(node="192.168.122.161", cmd=cmd)

        #TODO: to be removed
        pp.pprint(ret)
    
        RR.rlogger.info(ret)

        if ret['error_code'] != 0:
            raise Exception(ret['msg'])
    
    except Exception as e:
        RR.rlogger.error(e)

    
    return ret


if __name__ == "__main__":
    R.establish_connection()
    #volume_mount("10.70.43.228","test-vol","test_dir")
    touch("test_file")
    mkdir("test_dir")
    ls()
   
