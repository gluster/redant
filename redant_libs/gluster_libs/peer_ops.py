class peer_ops:

    def peer_probe(self, server, node):
        """
        node: The node in the cluster where peer probe is to be run
        server: The server to probe
        """
        try:
        
            cmd = 'gluster --xml peer probe %s' % server

            self.rlog("Running %s on node %s" % (cmd,node))
            ret = self.execute_command(node=node, cmd=cmd)


            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])
            else:
                self.rlog("Successfully ran %s on %s " % (cmd, node))

        except Exception as error:
            self.rlog(error, 'E')
        return ret

    def peer_detach(self, node, server, force=False):
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
            
            if force:
                cmd = "gluster --xml peer detach %s force --mode=script" % server

            else:
                cmd = "gluster --xml peer detach %s --mode=script" % server
            
            self.rlog("Running %s on node %s" % (cmd,node))

            ret = self.execute_command(node, cmd)

            
            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])

            else:
                self.rlog("Successfully ran %s on node %s" % (cmd,node))

        except Exception as error:

            self.rlog(error, 'E')

        return ret


    def peer_status(self, node):
        """
        Checks the status of the peers
        """
        try:

            cmd = 'gluster --xml peer status'

            self.rlog("Running %s on node %s" % (cmd,node))

            ret = self.execute_command(node, cmd)

            if ret['error_code'] != 0: 
                raise Exception(ret['msg']['opErrstr'])

            else:
                self.rlog("Successfully ran %s on node %s" % (cmd,node))

                
        except Exception as error:
            self.rlog(error, 'E')

        return ret

    def pool_list(self, node):
        """
        runs the command gluster pool list on `node`
        """
        try:
            cmd = 'gluster --xml pool list' 

            self.rlog("Running %s on node %s" % (cmd,node))

            ret = self.execute_command(node, cmd)

            if ret['error_code'] != 0:
                raise Exception(ret['msg']['opErrstr'])

            else:
                self.rlog("Successfully ran %s on node %s" % (cmd,node))

        except Exception as error:
            self.rlog(error, 'E')
            
        return ret

