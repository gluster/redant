class VolumeOps:

    def volume_create(self,node: str,volname: str,
                      bricks_list: list,force: bool=False,
                      **kwargs):
        """Create the gluster volume with specified configuration
        Args:
            node(str): server on which command has to be executed
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
        Logging is done and exceptions are raised if required
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
            replica = f"replica {replica_count}"

        if arbiter_count is not None:
            arbiter = f"arbiter {arbiter_count}"

        if stripe_count is not None:
            stripe = f"stripe {stripe_count}"

        if disperse_count is not None:
            disperse = f"disperse {disperse_count}"

        if disperse_data_count is not None:
            disperse_data = f"disperse-data {disperse_data_count}"

        if redundancy_count is not None:
            redundancy = f"redundancy {redundancy_count}"

        if transport_type is not None:
            transport = f"transport {transport_type}"
        
        bricks_list_string = ' '.join(bricks_list)
        cmd = (f"gluster volume create {volname} {replica} "
               f"{arbiter} {stripe} {disperse} {disperse_data} "
               f"{redundancy} {transport} {bricks_list_string} --xml "
               "--mode=script")
        
        if force:
            cmd = cmd + " force"
        
        self.rlog(f"Running {cmd} on node {node}", 'I')
        
        ret =  self.execute_command(node=node,cmd=cmd)
        
        if int(ret['msg']['opRet'])!=0:
            self.rlog(ret['msg']['opErrstr'],'E')
            raise Exception(ret['msg']['opErrstr'])
        else:    
            self.rlog(f"Successfully ran {cmd} on {node}",'I')


    def volume_start(self,node: str,volname: str,force: bool=False):
        """Starts the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Kwargs:
            force (bool): If this option is set to True, then start volume
                will get executed with force option. If it is set to False,
                then start volume will get executed without force option
        Logging is done and exceptions are raised if required
        """

        if force:
            cmd = f"gluster volume start {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume start {volname} --mode=script --xml"
            
        self.rlog(f"Running {cmd} on node {node}", 'I')
        
        ret = self.execute_command(node=node,cmd=cmd)
        
        if int(ret['msg']['opRet'])!=0:
            self.rlog(ret['msg']['opErrstr'],'E')
            raise Exception(ret['msg']['opErrstr'])   
        else:    
            self.rlog(f"Successfully ran {cmd} on {node}",'I')


    def volume_stop(self,node: str,volname: str,force: bool=False):
        """Starts the gluster volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Kwargs:
            force (bool): If this option is set to True, then start volume
                will get executed with force option. If it is set to False,
                then start volume will get executed without force option
        Logging is done and exceptions are raised if required
        """

        if force:
            cmd = f"gluster volume stop {volname} force --mode=script --xml"
        else:
            cmd = f"gluster volume stop {volname} --mode=script --xml"
        
        self.rlog(f"Running {cmd} on node {node}", 'I')
        
        ret = self.execute_command(node=node,cmd=cmd)
        
        if int(ret['msg']['opRet'])!=0:
            self.rlog(ret['msg']['opErrstr'],'E')
            raise Exception(ret['msg']['opErrstr'])
        else:
            self.rlog(f"Successfully ran {cmd} on {node}",'I')


    def volume_delete(self,node: str,volname: str):
        """Deletes the gluster volume if given volume exists in
           gluster and deletes the directories in the bricks
           associated with the given volume
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Logging is done and exceptions are raised if required
        """
        
        cmd = f"gluster volume delete {volname} --mode=script --xml"
        
        self.rlog(f"Running {cmd} on node {node}", 'I')
        
        ret = self.execute_command(node=node,cmd=cmd)
        
        if int(ret['msg']['opRet'])!=0:
            self.rlog(ret['msg']['opErrstr'],'E')
            raise Exception(ret['msg']['opErrstr'])  
        else:    
            self.rlog(f"Successfully ran {cmd} on {node}",'I')
        

    def volume_info(self,node: str,volname: str='all') -> dict:
        """Gives volume information
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Returns:
            a dictionary with volume information.
        Logging is done and exceptions are raised if required
        """
        
        cmd = f"gluster volume info {volname} --xml"
        
        self.rlog(f"Running {cmd} on node {node}", 'I')
        
        ret = self.execute_command(node=node,cmd=cmd)
        
        if int(ret['msg']['opRet'])!=0:
            self.rlog(ret['msg']['opErrstr'],'E')
            raise Exception(ret['msg']['opErrstr'])
        else:    
            self.rlog(f"Successfully ran {cmd} on {node}",'I')
            
        volume_info = ret['msg']
        
        ret_val = volume_info['volInfo']['volumes']['volume']

        return ret_val
