"""
Shared storage ops module deals with the functions related to shared storage
operations.
"""

from time import sleep
from common.ops.abstract_ops import AbstractOps


class SharedStorageOps(AbstractOps):
    """
    Class which is responsible for methods for shared storage related
    operations.
    """
    def enable_shared_storage(self, node: str) -> bool:
        """
        Enables the shared storage

        Args:
            node (str) : Node on which command is to be executed

        Returns:
            bool : True if successfully enabled shared storage.
                   False otherwise.
        """
        option = {"cluster.enable-shared-storage": "enable"}

        try:
            self.set_volume_options("all", option, node)

        except Exception as error:
            self.logger.error(f"Failed to enable shared storage: {error}")
            return False

        return True

    def disable_shared_storage(self, node: str) -> bool:
        """
        Disable the shared storage

        Args:
            node (str) : Node on which command is to be executed

        Returns:
            bool : True if successfully disabled shared storage.
                   False otherwise.
        """
        option = {"cluster.enable-shared-storage": "disable"}

        try:
            self.set_volume_options("all", option, node)

        except Exception as error:
            self.logger.error(f"Failed to disable shared storage: {error}")
            return False

        return True

    def is_shared_volume_mounted(self, node: str, is_mounted=True,
                                 timeout: int = 20) -> bool:
        """
        Checks if shared storage volume is mounted

        Args:
            node (str) : Node on which command is to be executed
            is_mounted (bool): True, if the volume is expected to be mounted,
                               False if it is not expected to be mounted.
        Optional:
            timeout(int) : Maximum time allowed to check for shared volume

        Returns:
            bool : True if shared storage volume is mounted/unmounted as
                   expected, False otherwise.
        """
        counter = 0
        path = "/run/gluster/shared_storage"
        ip_node = self.convert_hosts_to_ip(node)[0]
        while counter < timeout:
            ret = self.execute_abstract_op_node("df -h", ip_node, False)
            if is_mounted and path in " ".join(ret['msg']):
                self.logger.info("Shared storage is mounted")
                return True
            elif not is_mounted and path not in " ".join(ret['msg']):
                self.logger.info("Shared storage not mounted")
                return True

            sleep(2)
            counter += 2

        return False

    def check_gluster_shared_volume(self, node: str,
                                    present: bool = True,
                                    timeout: int = 20) -> bool:
        """
        Check gluster shared volume present or absent.

        Args:
            node (str) : Node on which command is to be executed
        Optional:
            present (bool) : True if you want to check presence
                             False if you want to check absence.
            timeout(int) : Maximum time allowed to check for shared volume

        Returns:
            bool : True if gluster_shared_storage volume present/absent in
                   volume list as expected, False otherwise.
        """
        counter = 0
        self.logger.info("Waiting for shared storage to be"
                         " created/deleted")

        while counter < timeout:
            vol_list = self.get_volume_list(node)
            if vol_list is None:
                self.logger.error("Failed to get vol list")
                return False
            if present and "gluster_shared_storage" in vol_list:
                return True
            elif (not present
                  and "gluster_shared_storage" not in vol_list):
                return True
            else:
                sleep(2)
                counter += 2

        if present:
            self.logger.info("Shared storage volume is not created")
        else:
            self.logger.info("Shared storage volume is not deleted")

        return False
