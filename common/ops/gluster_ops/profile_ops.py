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

    def profile_start(self, volname: str, node: str = None,
                      excep: bool = True) -> dict:
        """
        Start profile on the specified volume.
        Args:
            volname (str): Volume on which profile has to be started.
            node (str): Node on which command has to be executed.
            excep (bool): exception flag to bypass the exception if the
                          volume status command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
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

        ret = self.execute_abstract_op_node(cmd, node, excep)

        return ret

    def profile_info(self, volname: str, node: str = None,
                     options: str = '', excep: bool = True) -> dict:
        """
        Run profile info on the specified volume.
        Args:
            volname (str): Volume for which profile info has to be retrived.
            node (str): Node on which command has to be executed.
            options (str): Options can be
                           [peek|incremental [peek]|cumulative|clear].If not
                           given the function returns the output of gluster
                           volume profile <volname> info.
            excep (bool): exception flag to bypass the exception if the
                          volume status command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
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
        if options != '' and not self.check_profile_options(options):
            return None
        cmd = f"gluster volume profile {volname} info {options}"

        ret = self.execute_abstract_op_node(cmd, node, excep)

        return ret

    def profile_stop(self, volname: str, node: str = None,
                     excep: bool = True) -> dict:
        """Stop profile on the specified volume.
        Args:
            volname (str): Volume on which profile has to be stopped.
            node (str): Node on which command has to be executed.
            excep (bool): exception flag to bypass the exception if the
                          volume status command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
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

        ret = self.execute_abstract_op_node(cmd, node, excep)

        return ret

    def check_profile_options(self, options: str) -> bool:
        """
        Helper function to validate the profile options.
        Args:
            options (str): Options can be nothing or
            [peek|incremental [peek]|cumulative|clear].
        Returns:
            True: If valid option is given.
            False: If invalid option is given
        """

        list_of_options = ['peek', 'incremental', 'incremental peek',
                           'cumulative', 'clear']
        if options not in list_of_options:
            self.logger.error("Invalid profile info option given.")
            return False
        return True
