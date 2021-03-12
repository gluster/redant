class io_ops:

    def volume_mount(self ,node :str ,server :str ,volname :str, dir :str ,force : bool=False):
        '''Mounts the gluster volumes
        
        node: The node in the cluster where volume mount is to be run
        server: HOST_NAME or IP address
        volname: Name of volume to be mounted
        dir: The path of the mount directory(mount point)
        '''

        try:
            self.rlog("Volume Mount Command initiated" , "I")
            
            if force:
                cmd = f"mount -t --force glusterfs {server}:/{volname} /{dir}"
            else:
                cmd = f"mount -t glusterfs {server}:/{volname} /{dir}"
            self.rlog(f"Running {cmd} on node {node}", 'I')
            ret = self.execute_command(node=node,cmd=cmd)    
                    
            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
            else:
                self.rlog("Successfully ran {cmd} on {node} ", 'I')
        
        except Exception as e:
            self.rlog(e , 'E') 
        return ret 

    def touch(self ,file_name :str ,node :str):
        """Creates a regular empty file
        
        file_name: The name of the file to be created
        node: The node in the cluster where the command is to be run
        """

        try:            
            self.rlog("Creating File" , "I") 

            cmd = "touch {}".format(file_name)
            self.rlog(f"Running {cmd} on node {node}", 'I')
            ret = self.execute_command(node=node, cmd=cmd)
            
            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
            else:
                self.rlog("Successfully ran {cmd} on {node} ", 'I')
        
        except Exception as e:
            self.rlog(e , 'E')    
        return ret

    def mkdir(self ,dir_name : str ,node :str):
        '''Creates a directory
        
        dir_name: The name of the directory to be created
        node: The node in the cluster where the command is to be run
        '''

        try:
            self.rlog("Creating Directory" , "I")        
            
            cmd = f'mkdir -p /{dir_name}'
            self.rlog(f"Running {cmd} on node {node}", 'I')
            ret = self.execute_command(node=node, cmd=cmd)
            
            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
            else:
                self.rlog("Successfully ran {cmd} on {node} ", 'I')
        
        except Exception as e:
            self.rlog(e, 'E')    
        return ret

    def ls(self ,node :str):
        '''List the directory contents
        
        node: The node in the cluster where the command is to be run
        '''

        try:
            self.rlog("List the files on root directory" , "I")
              
            cmd = 'ls'
            self.rlog(f"Running {cmd} on node {node}", 'I')
            ret = self.execute_command(node=node, cmd=cmd)

            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
            else:
                self.rlog("Successfully ran {cmd} on {node} ", 'I')
        
        except Exception as e:
            self.rlog(e , 'E')    
        return ret
