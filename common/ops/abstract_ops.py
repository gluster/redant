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

    def execute_abstract_op_node(self, cmd: str, node: str = None,
                                 excep: bool = True):
        """
        Calls the function in the remote executioner to execute
        commands on the nodes. Logging is also performed along
        with handling exceptions while executng the commands.
        Args:
            cmd  (str): the command to be executed by the rexe
        Kwargs:
            node (str): the node on which the command as to be executed.
                        If the node is None then the rexe chooses the
                        node randomly and executes the command on it.
            excep (bool): exception flag to bypass the exception if the
                          cmd fails. If set to False the exception is
                          bypassed and value from remote executioner is
                          returned. Defaults to True
            
        """
        self.logger.info(f"Running {cmd} on {node}")

        ret = self.execute_command(cmd, node)

        if not excep:
            return ret

        if ret['error_code'] != 0:
            self.logger.error(ret['error_msg'])
            raise Exception(ret['error_msg'])
        elif isinstance(ret['msg'], (OrderedDict, dict)):
            if int(ret['msg']['opRet']) != 0:
                self.logger.error(ret['msg']['opErrstr'])
                raise Exception(ret['msg']['opErrstr'])

        return ret

    def execute_abstract_op_multinode(self, cmd: str, node: list = None):
        """
        Calls the function in the remote executioner to execute
        commands on the nodes. Logging is also performed along
        with handling exceptions while executng the commands.
        Args:
            cmd  (str): the command to be executed by the rexe
            node (list): the list of nodes on which the command as to be
                         executed. If the node is None then the rexe chooses
                         the node randomly and executes the command on it.
        """
        self.logger.info(f"Running {cmd} on {node}")

        ret = self.execute_command_multinode(cmd, node)

        for each_ret in ret:
            if each_ret['error_code'] != 0:
                self.logger.error(each_ret['msg']['opErrstr'])
                raise Exception(each_ret['msg']['opErrstr'])
            elif isinstance(each_ret['msg'], (OrderedDict, dict)):
                if int(each_ret['msg']['opRet']) != 0:
                    self.logger.error(each_ret['msg']['opErrstr'])
                    raise Exception(each_ret['msg']['opErrstr'])

        return ret
