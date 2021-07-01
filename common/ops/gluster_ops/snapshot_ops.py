"""
This file contains one class - SnapshotOps wich holds
operations on the enable, disable the features.uss option,
check for snapd process.
"""
from common.ops.abstract_ops import AbstractOps


class SnapshotOps(AbstractOps):
    """
    SnapshotOps class provides APIs to enable, disable
    the features.uss option, check for snapd process.
    """

    def enable_uss(self, node: str, volname: str,
                   excep: bool = True) -> dict:
        """
        Enables uss on the specified volume

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Optional:
            excep (bool): exception flag to bypass the exception if the
                          enable uss command fails. If set to False
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
        cmd = f"gluster volume set {volname} features.uss enable --mode=script"
        ret = self.execute_abstract_op_node(cmd, node, excep)
        return ret

    def disable_uss(self, node: str, volname: str,
                    excep: bool = True) -> dict:
        """
        Disable uss on the specified volume

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name
        Optional:
            excep (bool): exception flag to bypass the exception if the
                          disable uss command fails. If set to False
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
        cmd = (f"gluster volume set {volname} features.uss disable"
               " --mode=script")
        ret = self.execute_abstract_op_node(cmd, node, excep)
        return ret

    def is_uss_enabled(self, node: str, volname: str) -> bool:
        """
        Check if uss is Enabled on the specified volume

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name

        Returns:
            bool : True if successfully enabled uss on the volume.
                   False otherwise.
        """
        option_dict = self.get_volume_options(volname, "uss", node, False)
        if not option_dict:
            self.logger.error(f"USS is not set on the volume {volname}")
            return False

        if ('features.uss' in option_dict
           and option_dict['features.uss'] == 'enable'):
            return True

        return False

    def is_uss_disabled(self, node: str, volname: str) -> bool:
        """
        Check if uss is Disabled on the specified volume

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name

        Returns:
            bool : True if successfully enabled uss on the volume.
                   False otherwise.
        """
        option_dict = self.get_volume_options(volname, "uss", node, False)
        if not option_dict:
            self.logger.error(f"USS is not set on the volume {volname}")
            return False

        if ('features.uss' in option_dict
           and option_dict['features.uss'] == 'disable'):
            return True

        return False

    def is_snapd_running(self, node: str, volname: str) -> bool:
        """
        Checks if snapd is running on the given node

        Args:
            node (str): Node on which cmd has to be executed.
            volname (str): volume name

        Returns:
            bool: True on success, False otherwise
        """
        vol_status = self.get_volume_status(volname, node)

        if vol_status is None:
            self.logger.error("Failed to get volume status in "
                              "is_snapd_running()")
            return False

        is_enabled = False
        online_status = False
        if 'node' in vol_status[volname]:
            for brick in vol_status[volname]['node']:
                if (brick['hostname'] == "Snapshot Daemon"
                   and brick['path'] == node):
                    is_enabled = True
                    if brick['status'] != '1':
                        online_status = False
                        break

        if not is_enabled:
            self.logger.error("Snapshot Daemon is not enabled for "
                              f"volume {volname}")
            return False
        if not online_status:
            self.logger.error("Snapshot Daemon is not running on node"
                              f" {node}")
            return False
        return True
