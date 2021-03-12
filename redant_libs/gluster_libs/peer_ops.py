class peer_ops:

    def peer_probe(self, server: str, node: str):
        """
        node: The node in the cluster where peer probe is to be run
        server: The server to probe
        """
        try:
            self.rlog("Redant test framework started")
            cmd = 'gluster --xml peer probe %s' % server

            self.rlog("Running %s on node %s" % (cmd,node))
            ret = self.execute_command(node=node, cmd=cmd)
        
            self.rlog(ret)

            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])

        except Exception as error:
            self.rlog(error, 'E')
        return ret

    def peer_detach(self, node: str, server: str, force: bool=False):
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
            self.rlog("Peer detach initiated")
            if force:
                cmd = "gluster --xml peer detach %s force --mode=script" % server
            else:
                cmd = "gluster --xml peer detach %s --mode=script" % server
            ret = self.execute_command(node, cmd)
            self.rlog(ret)

            ret['error_code'] = 2
            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
        except Exception as error:
            self.rlog(error, 'E')
        return ret


    def peer_status(self, node: str):
        """
        Checks the status of the peers
        """
        try:
            cmd = 'gluster --xml peer status'
            self.rlog("Running %s" % cmd)
            ret = self.execute_command(node, cmd)
            self.rlog(ret)  
            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
        except Exception as error:
            self.rlog(error, 'E')
        return ret

    def pool_list(self, node: str):
        """
        runs the command gluster pool list on `node`
        """
        try:
            cmd = 'gluster --xml pool list' 
            self.rlog("Running the command %s" % cmd)
            ret = self.execute_command(node, cmd)
            self.rlog(ret)
            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
        except Exception as error:
            self.rlog(error, 'E')
        return ret

