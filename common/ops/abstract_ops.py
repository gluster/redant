"""
This file contains one class - AbstractOps which
is inherited by the ops library and the ops library
call the functions in the AbstractOps which in turn
call the funtions in the remote executioner which is
responsible for executing commands on the nodes.
"""
from collections import OrderedDict

class AbstractOps:
    """
    This class contains functions which is responsible for
    calling the funtions in the remote executioner for executing
    commands on the nodes
    """
    def execute_abstract_op_node(self, cmd : str, node : str=None):
        """
        Calls the function in the remote executioner to execute
        commands on the nodes. Logging is also performed along
        with handling exceptions while executng the commands.
        Args:
            cmd  (str): the command to be executed by the rexe
            node (str): the node on which the command as to be executed.
                        If the node is None then the rexe chooses the
                        node randomly and executes the command on it.
        """

        ret = self.execute_command(cmd, node)

        if(ret['error_code']!=0):
            self.logger.error(ret['error_msg'])
            raise Exception(ret['error_msg'])    
        elif isinstance(ret['msg'],OrderedDict) or isinstance(ret['msg'],dict):
            if int(ret['msg']['opRet']) != 0:
                self.logger.error(ret['msg']['opErrstr'])
                raise Exception(ret['msg']['opErrstr'])

<<<<<<< HEAD
=======
        self.logger.info(f"Successfully ran {cmd} on {ret['node']}")

>>>>>>> 16b28c6... Gluster ops modified to use abstract ops functionalities
        return ret
        
    def execute_abstract_op_multinode(self, cmd : str, node : list=None):
        """
        Calls the function in the remote executioner to execute
        commands on the nodes. Logging is also performed along
        with handling exceptions while executng the commands.
        Args:
            cmd  (str): the command to be executed by the rexe
            node (str): the node on which the command as to be executed.
                        If the node is None then the rexe chooses the
                        node randomly and executes the command on it.
        """
        ret = self.execute_command_multinode(cmd, node)
        for each_ret in ret:
            if each_ret['error_code'] != 0:
                self.logger.error(each_ret['msg']['opErrstr'])
                raise Exception(each_ret['msg']['opErrstr'])

            self.logger.info(f"Successfully ran {cmd} on {each_ret['node']}")
            
        return ret
        
        
        
