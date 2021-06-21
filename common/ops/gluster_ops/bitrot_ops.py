"""
This file contains one class - BitrotOps wich holds
operations on the start, stop, enable, disable of the bitrot
and scrub service.
"""
from common.ops.abstract_ops import AbstractOps


class BitrotOps(AbstractOps):
    """
    BitrotOps class provides APIs to start, stop
    the bitd, scrub process or enable/disable bitrot feature.
    """

    def enable_bitrot(self, volname: str, node: str,
                      excep: bool = True) -> dict:
        """
        Enables bitrot for given volume

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.
        Optional:
            excep (bool): exception flag to bypass the exception if the
                          bitrot enable command fails. If set to False
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
        """

        cmd = f"gluster volume bitrot {volname} enable --mode=script"
        ret = self.execute_abstract_op_node(cmd, node, excep)
        return ret

    def disable_bitrot(self, volname: str, node: str,
                       excep: bool = True) -> dict:
        """
        Disable bitrot for given volume

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.
        Optional:
            excep (bool): exception flag to bypass the exception if the
                          bitrot disable command fails. If set to False
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
        """

        cmd = f"gluster volume bitrot {volname} disable --mode=script"
        ret = self.execute_abstract_op_node(cmd, node, excep)
        return ret

    def is_bitrot_enabled(self, volname: str, node: str) -> bool:
        """
        Checks if bitrot is enabled on given volume

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            True on success, False otherwise
        """

        vol_dict = self.get_volume_options(volname, "features.bitrot", node)
        if vol_dict is None:
            return False

        if vol_dict["features.bitrot"] != 'on':
            return False

        return True

    def get_bitd_pid(self, node: str) -> str:
        """
        Gets bitd process id for the given node

        Args:
            node (str): Node on which cmd has to be executed.

        Returns:
            str: pid of the bitd process on success
            NoneType: None if command execution fails, errors.
        """

        cmd = "cat /var/lib/glusterd/bitd/run/bitd.pid"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            self.logger.error(f"Failed to get bitd pid for {node}")
            return None

        return ret['msg'][0].rstrip("\n")

    def get_scrub_process_pid(self, node: str) -> str:
        """
        Gets scrub process id for the given node

        Args:
            node (str): Node on which cmd has to be executed.

        Returns:
            str: pid of the scrub process on success
            NoneType: None if command execution fails, errors.
        """

        cmd = "cat /var/lib/glusterd/scrub/run/scrub.pid"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] != 0:
            self.logger.error(f"Failed to get scrub pid for {node}")
            return None

        return ret['msg'][0].rstrip("\n")

    def is_bitd_running(self, volname: str, node: str) -> bool:
        """
        Checks if bitd is running on the given node

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            True on success, False otherwise
        """

        vol_status = self.get_volume_status(volname, node)
        if vol_status is None:
            self.logger.error("Failed to get volume status")
            return False

        is_enabled = False
        online_status = False
        if 'node' in vol_status[volname]:
            for brick in vol_status[volname]['node']:
                if (brick['hostname'] == "Bitrot Daemon"
                   and brick['path'] == node):
                    is_enabled = True
                    if brick['status'] != '1':
                        online_status = False
                        break

        if not is_enabled:
            self.logger.error(f"Bitrot is not enabled for volume {volname}")
            return False
        if not online_status:
            self.logger.error(f"Bitrot Daemon is not running on node {node}")
            return False
        return True

    def is_scrub_process_running(self, node: str, volname: str) -> bool:
        """
        Checks if scrub process is running on the given node

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            True on success, False otherwise
        """

        vol_status = self.get_volume_status(volname, node)
        if vol_status is None:
            self.logger.error("Failed to get volume status")
            return False

        is_enabled = False
        online_status = False
        if 'node' in vol_status[volname]:
            for brick in vol_status[volname]['node']:
                if (brick['hostname'] == "Scrubber Daemon"
                   and brick['path'] == node):
                    is_enabled = True
                    if brick['status'] != '1':
                        online_status = False
                        break

        if not is_enabled:
            self.logger.error("Scrubber Daemon is not enabled for "
                              f"volume {volname}")
            return False
        if not online_status:
            self.logger.error("Scrubber Daemon is not running on node"
                              f" {node}")
            return False
        return True
