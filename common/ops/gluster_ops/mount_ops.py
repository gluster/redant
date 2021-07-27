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
                          mount command fails. If set to False
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

        cmd = f"mount.glusterfs {server}:/{volname} {path}"

        ret = self.execute_abstract_op_node(cmd, node, excep)
        if not excep and ret['error_code'] != 0:
            return ret

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
                          is_mounted command fails. If set to False
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

    def mount_snap(self, server: str, volname: str, snapname: str,
                   node: str, path: str, excep: bool = True) -> dict:
        """
        Args:
            server (str): Hostname or IP address
            volname (str): Name of volume whose snap is to be mounted
            snapname (str): Name of the snap which is to be mounted.
            path (str): The path of the mount directory(mount point)
            node (str): The node where snap mount is to be run
            excep (bool): exception flag to bypass the exception if the
                          snap mount command fails. If set to False
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

        cmd = f"mount.glusterfs {server}:/snaps/{snapname}/{volname} {path}"

        ret = self.execute_abstract_op_node(cmd, node, excep)
        if not excep and ret['error_code'] != 0:
            return ret

        self.es.add_new_snap_mountpath(snapname, node, path)
        return ret

    def unmount_snap(self, snapname: str, path: str, node: str,
                     excep: bool = True) -> dict:
        """
        Unmounts the gluster snpashot.
        Args:
            snpaname (str): The snapshot whose mt pt. is to be unmounted.
            path (str): The path of the mount directory(mount point).
            node (str): The node where snpa unmount is to be run.
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

        if not excep and ret['error_code'] != 0:
            return ret

        self.es.remove_snap_mountpath(snapname, node, path)
        return ret

    def unmount_all_snap(self):
        """
        Unmounts all snapshot mounts.
        """
        # Getting a list of snap mountpaths so that we can unmount them.
        snap_mnt_dict = self.es.get_snap_mnt_dict()
        for snap in snap_mnt_dict.keys():
            for client in snap_mnt_dict[snap].keys():
                for mntpath in snap_mnt_dict[snap][client]:
                    self.unmount_snap(snap, mntpath, client)

    def view_snap_from_mount(self, mounts_obj: list, snaps: list) -> bool:
        """
        Method to verify if the stated snaps are present under the .snaps
        directory.

        Args:
            mount_obj (list): The mount_obj consists of client and mountpath
            combination of dictionaries in a list.
            snaps (list/str): List of snap names.

        Returns:
            bool: True if all the said snapnames in the snaps list are present
            under the .snaps dir, else False.
        """
        if not isinstance(snaps, list):
            snaps = [snaps]

        ret_list = []
        for mountob in mounts_obj:
            cmd = f'ls {mountob["mountpath"]}/.snaps/'
            ret = self.execute_abstract_op_node(cmd, mountob["client"])
            listing = [listval.strip() for listval in ret['msg']]
            ret_list.append(listing)
            if set(listing) != set(snaps):
                return False
        return True
