"""
This file contains one class - RebalanceOps which
holds rebalance operation functions which will be called
from the test case.
"""
import time
from common.ops.abstract_ops import AbstractOps


class RebalanceOps(AbstractOps):
    """
    RebalanceOps class provides APIs to perform rebalance
    operations like rebalance_start, rebalance_stop, rebalance_status,
    get_rebalance_status, wait_for_fix_layout_to_complete,
    wait_for_rebalance_to_complete etc.
    """

    def rebalance_start(self, volname: str, node: str,
                        fix_layout: bool = False, force: bool = False):
        """
        Starts rebalance on the given volume.
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Kwargs:
            fix_layout (bool) : If this option is set to True, then rebalance
                                start will get execute with fix-layout option.
                                If set to False, then rebalance start will get
                                executed without fix-layout option
            force (bool): If this option is set to True, then rebalance start
                          will get execute with force option. If it is set to
                          False, then rebalance start will get executed
                          without force option
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        """

        flayout = ''
        if fix_layout:
            flayout = "fix-layout"

        frce = ''
        if force:
            frce = 'force'

        if fix_layout and force:
            self.logger.info("Both fix-layout and force option is "
                             "specified. Ignoring force option")
            frce = ''

        cmd = f"gluster volume rebalance {volname} {flayout} start {frce}"
        ret = self.execute_abstract_op_node(cmd, node)

        return ret

    def rebalance_stop(self, volname: str, node: str):
        """
        Stops rebalance on the given volume.
        Example:
            rebalance_stop("abc.com", testvol)
        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Returns:
            ret: A dictionary consisting
                        - Flag : Flag to check if connection failed
                        - msg : message
                        - error_msg: error message
                        - error_code: error code returned
                        - cmd : command that got executed
                        - node : node on which the command got executed

        """

        cmd = f"gluster volume rebalance {volname} stop"
        ret = self.execute_abstract_op_node(cmd, node)

        return ret

    def get_rebalance_status(self, volname: str, node: str):
        """
        Parse the output of 'gluster vol rebalance status' command
        for the given volume
        Args:
            node (str): Node on which command has to be executed.
            volname (str): volume name
        Returns:
            dict: rebalance status will be in dict format
        """

        cmd = f"gluster volume rebalance {volname} status --xml"
        ret = self.execute_abstract_op_node(cmd, node)

        return ret['msg']['volRebalance']

    def wait_for_fix_layout_to_complete(self, node: str, volname: str,
                                        timeout=300):
        """
        Waits for the fix-layout to complete
        Args:
            node (str): Node on which command has to be executed.
            volname (str): volume name
        Kwargs:
            timeout (int): timeout value in seconds to wait for rebalance
                to complete
        Returns:
            True on success, False otherwise
        Examples:
            >>> wait_for_fix_layout_to_complete("abc.com", "testvol")
        """

        count = 0
        while count < timeout:
            status_info = self.get_rebalance_status(volname, node)

            status = status_info['aggregate']['statusStr']
            if status == 'fix-layout completed':
                self.logger.info("Fix-layout is successfully completed")
                return True
            if status == 'fix-layout failed':
                self.logger.error("Fix-layout failed on one or more nodes."
                                  "Check rebalance status for more details")
                return False

            time.sleep(10)
            count = count + 10
        self.logger.error("Fix layout has not completed. Wait timeout.")
        return False

    def wait_for_rebalance_to_complete(self, volname: str,
                                       node: str, timeout=300):
        """
        Waits for the rebalance to complete
        Args:
            node (str): Node on which command has to be executed.
            volname (str): volume name
        Kwargs:
            timeout (int): timeout value in seconds to wait for rebalance
                to complete
        Returns:
            True on success, False otherwise
        Examples:
            >>> wait_for_rebalance_to_complete("abc.com", "testvol")
        """

        count = 0
        while count < timeout:
            status_info = self.get_rebalance_status(volname, node)

            status = status_info['aggregate']['statusStr']
            if status == 'completed':
                self.logger.info("Rebalance is successfully completed")
                return True
            if status == 'failed':
                self.logger.error(" Rebalance failed on one or more nodes."
                                  "Check rebalance status for more details")
                return False

            time.sleep(10)
            count = count + 10
        self.logger.error(
            "Rebalance operation has not completed. Wait timeout.")
        return False
