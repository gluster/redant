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

    def scheduler_add_jobs(self, node: str, jobname: str, scheduler: str,
                           volname: str, excep: bool = True) -> dict:
        """
        Add snapshot scheduler Jobs on given node

        Args:
            node (str): Node on which cmd has to be executed.
            jobname (str): scheduled Jobname
            scheduler (str): "* * * * *"
            * * * * *
            | | | | |
            | | | | +---- Day of the Week   (range: 1-7, 1 standing for Monday)
            | | | +------ Month of the Year (range: 1-12)
            | | +-------- Day of the Month  (range: 1-31)
            | +---------- Hour              (range: 0-23)
            +------------ Minute            (range: 0-59)

            volname (str): Volume name to schedule a job.
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
            scheduler_add_jobs("abc.com", "jobname", "*/10 * * * *", "volname")

        """
        cmd = f'snap_scheduler.py add "{jobname}" "{scheduler}" {volname}'
        return self.execute_abstract_op_node(cmd, node, excep)

    def scheduler_list(self, node: str, excep: bool = True) -> dict:
        """
        Executes snapshot scheduler list command

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
            scheduler_list("abc.com")
        """
        cmd = "snap_scheduler.py list"
        return self.execute_abstract_op_node(cmd, node, excep)

    def scheduler_delete(self, node: str, jobname: str,
                         excep: bool = True) -> dict:
        """
        Deletes the already scheduled job

        Args:
            node (str): Node on which cmd has to be executed.
            jobname (str): scheduled Jobname
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
            scheduler_delete("abc.xyz.com", "Job1")
        """
        cmd = f"snap_scheduler.py delete {jobname}"
        return self.execute_abstract_op_node(cmd, node, excep)
