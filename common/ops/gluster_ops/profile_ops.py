"""
This file contains one class - ProfileOps which
holds profile operation functions which will be called
from the test case.
"""

from common.ops.abstract_ops import AbstractOps


class ProfileOps(AbstractOps):
    """
    Profile Ops class provides APIs to perform profile
    operations like profile_start, profile_stop, profile_info,
    check_profile_options etc.
    """

    def profile_start(self, volname: str, node: str) -> dict:
        """
        Start profile on the specified volume.
        Args:
            volname (str): Volume on which profile has to started.
            node (str): Node on which command has to be executed.
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed

        Example:
            profile_start(node, "testvol")
        """
        cmd = f"gluster volume profile {volname} start"

        ret = self.execute_abstract_op_node(cmd, node)

        return ret

    def profile_info(self, volname: str, node: str,
                     options: str = '') -> dict:
        """
        Run profile info on the specified volume.
        Args:
            volname (str): Volume for which profile info has to be retrived.
            node (str): Node on which command has to be executed.
        Kwargs:
            options (str): Options can be
            [peek|incremental [peek]|cumulative|clear].If not given the
            function returns the output of gluster volume profile <volname>
            info.
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
            None: If invalid option is given.
        Example:
            profile_info(node, "testvol")
        """
        if not self.check_profile_options(options):
            return None
        cmd = f"gluster volume profile {volname} info {options}"

        ret = self.execute_abstract_op_node(cmd, node)

        return ret

    def profile_stop(self, volname: str, node: str) -> dict:
        """Stop profile on the specified volume.
        Args:
            volname (str): Volume on which profile has to be stopped.
            node (str): Node on which command has to be executed.
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        Example:
            profile_stop(node, "testvol")
        """
        cmd = f"gluster volume profile {volname} stop"

        ret = self.execute_abstract_op_node(cmd, node)

        return ret

    def check_profile_options(self, options: str) -> bool:
        """Helper function to valid if profile options.
        Args:
            options (str): Options can be nothing or
            [peek|incremental [peek]|cumulative|clear].
        Returns:
            True: If valid option is given.
            False: If invalid option is given
        """

        list_of_options = ['peek', 'incremental', 'incremental peek',
                           'cumulative', 'clear', '']
        if options not in list_of_options:
            self.logger.error("Invalid profile info option given.")
            return False
        return True
