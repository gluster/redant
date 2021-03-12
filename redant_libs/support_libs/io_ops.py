import sys
import os

class io_ops:

    def volume_mount(self ,node , server , volname , dir,force=False):
        try:
            self.log("Volume Mount Command initiated")
            
            if force:
                cmd = "mount -t --force glusterfs %s:/%s /%s" % (server,volname,dir)
            else:
                cmd = "mount -t glusterfs %s:/%s /%s" % (server,volname,dir)
            ret = self.execute_command(node=node,cmd=cmd)    
            
            self.log(ret)    
        
            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
        
        except Exception as e:
            self.rlog(e) 
        return ret 

    def touch(self, file_name , node):

        try:
            """Creates a regular empty file"""
            self.rlog("Creating File") 

            cmd = "touch {}".format(file_name)
            ret = self.execute_command(node=node, cmd=cmd)

            self.rlog(ret)

            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
        
        except Exception as e:
            self.rlog(e)    
        return ret

    def mkdir(self,dir_name, node):

        try:
            self.rlog("Creating Directory")
        
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            cmd = 'mkdir -p /%s/%s' % (ROOT_DIR , dir_name)  
            ret = self.execute_command(node=node, cmd=cmd)
        
            self.rlog(ret)

            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
        
        except Exception as e:
            self.rlog(e)    
        return ret

    def ls(self , node):

        try:
            self.rlog("List the files on root directory")

            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))    
            cmd = 'ls /%s'% ROOT_DIR
            ret = self.execute_command(node=node, cmd=cmd)

            self.rlog(ret)

            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
        
        except Exception as e:
            self.rlog(e)    
        return ret
