import sys

sys.path.append("./odinControl")

print(sys.path,"\n\n\n")

from rexe.rexe import Rexe

from redant_resources import Redant_Resources as RR

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

def create_file_using_touch(self, file_name):

    """Creates a regular empty file"""
    RR.rlogger.info("Creating File")

    
    cmd = "touch {}".format(file_name)

    ret = R.execute_command(node="192.168.122.161", cmd=cmd)

    #TODO: to be removed
    pp.pprint(ret)
    
    RR.rlogger.info(ret)
    return ret


def create_dir(self,dir_name):

    RR.rlogger.info("Creating Directory")
    
    cmd = 'mkdir -p /root_dir/'+dir_name+'{1..3}'
      

    ret = R.execute_command(node="192.168.122.161", cmd=cmd)

    #TODO: to be removed
    pp.pprint(ret)
    
    RR.rlogger.info(ret)
    return ret


def list_files_on_root_dir():

    RR.rlogger.info("List the files on root directory")
    
    cmd = 'ls /root_dir'

    ret = R.execute_command(node="192.168.122.161", cmd=cmd)

    #TODO: to be removed
    pp.pprint(ret)
    
    RR.rlogger.info(ret)
    return ret



if __name__ == "__main__":
    R.establish_connection()
    #volume_mount("10.70.43.228","test-vol","test_dir")
    create_file_using_touch("test_file")
    create_dir("test_dir")
    list_files_on_root_dir()
   
