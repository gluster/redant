"""
This file contains one class - SnapSchedulerOps wich holds
operations like enable, disable, init and few others on the snap scheduler
"""
from common.ops.abstract_ops import AbstractOps


class SnapSchedulerOps(AbstractOps):
    """
    SnapSchedulerOps class provides APIs to enable, disable,
    init and few others on the scheduler ops.
    """
    def scheduler_init(self, servers: list) -> bool:
        """
        Initialises snapshot scheduler

        Args:
            servers(list): List of servers on which cmd has to be executed.
            excep (bool): Whether to handle exception or not.
                          By default it is True.

        Returns:
            bool: True on Success, else False on failure

        Example:
            scheduler_init("abc.com")
        """
        if not isinstance(servers, list):
            servers = [servers]

        cmd = "snap_scheduler.py init"
        for server in servers:
            ret = self.execute_abstract_op_node(cmd, server, False)
            if ret['error_code'] != 0:
                self.logger.error("Unable to initialize scheduler on "
                                  f"{server}")
                return False

        return True

    def scheduler_enable(self, node: str, excep: bool = True) -> dict:
        """
        Enables snapshot scheduler on given node

        Args:
            node (str): Node on which cmd has to be executed.
            excep (bool): Whether to handle exception or not.
                          By default it is True.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

         Example:
            scheduler_enable("abc.com")
        """

        cmd = "snap_scheduler.py enable"
        return self.execute_abstract_op_node(cmd, node, excep)

    def scheduler_disable(self, node: str, excep: bool = True) -> dict:
        """
        Disable snapshot scheduler on given node

        Args:
            node (str): Node on which cmd has to be executed.
            excep (bool): Whether to handle exception or not.
                          By default it is True.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

         Example:
            scheduler_disable("abc.com")
        """

        cmd = "snap_scheduler.py disable"
        return self.execute_abstract_op_node(cmd, node, excep)

    def scheduler_status(self, node: str, excep: bool = True) -> dict:
        """
        Executes snapshot scheduler status command

        Args:
            node (str): Node on which cmd has to be executed.
            excep (bool): Whether to handle exception or not.
                          By default it is True.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        Example:
            scheduler_status("abc.xyz.com")
        """

        cmd = "snap_scheduler.py status"
        return self.execute_abstract_op_node(cmd, node, excep)
