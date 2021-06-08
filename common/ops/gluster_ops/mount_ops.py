"""
This file contains one class - MountOps which
holds mount related APIs which will be called
from the test case.
"""
from time import sleep
from common.ops.abstract_ops import AbstractOps


class MountOps(AbstractOps):
    """
    MountOps class provides APIs to perform operations
    related to volume mount like mount, unmount, is_mounted, is_unmounted
    """

    def volume_mount(self, server: str, volname: str,
                     path: str, node: str = None, excep: bool = True):
        """
        Mounts the gluster volume to the client's filesystem.
        Args:
            server (str): Hostname or IP address
            volname (str): Name of volume to be mounted
            path (str): The path of the mount directory(mount point)
            node (str): The client node in the cluster where volume
                        mount is to be run
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

        """

        cmd = f"mount -t glusterfs {server}:/{volname} {path}"

        ret = self.execute_abstract_op_node(cmd, node, excep)
        self.es.add_new_mountpath(volname, node, path)
        return ret

    def volume_unmount(self, volname: str, path: str, node: str = None,
                       excep: bool = True):
        """
        Unmounts the gluster volume .
        Args:
            volname (str): The volume whose mt pt. is to be unmounted.
            path (str): The path of the mount directory(mount point)
            node (str): The client node in the cluster where volume
                        unmount is to be run
            excep (bool): To bypass or not to bypass the exception handling.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """

        cmd = f"umount {path}"

        ret = self.execute_abstract_op_node(cmd, node, excep)
        self.es.remove_mountpath(volname, node, path)
        return ret

    def is_mounted(self, volname: str, mpath: str, mclient: str, mserver: str):
        """
        Check if the volume is already mounted or not
        Args:
            volname (str): Name of volume to be checked
            mpath (str): The path of the mount directory(mount point)
            mclient (str): The client node in the cluster where volume
                           is to be mounted
            mserver (str): Server to which volume is mounted to
            excep (bool): exception flag to bypass the exception if the
                          volume status command fails. If set to False
                          the exception is bypassed and value from remote
                          executioner is returned. Defaults to True
        Returns:
            bool: True if volume is mounted, False otherwise
        """
        # python will error on missing arg, so just checking for empty args
        if not volname or not mpath or not mserver or not mclient:
            self.logger.error("Missing arguments for mount.")
            return False

        cmd = f"mount | egrep '{volname} | {mpath}' | grep \'{mserver}\'"
        ret = self.execute_abstract_op_node(cmd, mclient, False)
        if ret['error_code'] == 0:
            self.logger.debug(f"Volume {volname} is mounted at"
                              f" {mclient}:{mpath}")
            return True
        else:
            self.logger.debug(f"Volume {volname} is not mounted at"
                              f" {mclient}:{mpath}")
            return False

    def get_fuse_process_count(self, node: str) -> int:
        """
        Get the fuse process count for a given node.

        Args:
            node (str): Node on which fuse process has to be counted.

        Returns:
            int: Number of fuse processes running on the node.
            None: If the command fails to execute.
        """
        ret = self.execute_abstract_op_node("pgrep -cf 'glusterfs.*fuse'",
                                            node, False)
        if ret['error_code'] == 0:
            count_of_proc = int(ret['msg'][0].rstrip('\n'))
            return count_of_proc
        else:
            return None

    def wait_for_mountpoint_to_connect(self, mountpoint: str,
                                       client_node: str,
                                       timeout: int = 20):
        """
        This function waits for mountpoint to get connected.
        A failed mountpoint connection results in exception
        'Transport endpoint not connected'.

        Args:
            mountpoint (str) : the mountpoint to check
            client_node (str): client node to execute the command
            timeout (int) : Timeout by default 20s.
                            Moreover, no one likes to wait forever :)

        Returns:
            True if mountpoint gets connected within the timeout
            else False.

        """
        cmd = f"stat -c '%a' {mountpoint}"
        count = 0
        while count <= timeout:
            ret = self.execute_abstract_op_node(cmd,
                                                client_node,
                                                False)
            if ret['error_code'] == 0:
                return True
            sleep(1)
            count += 1
        return False
