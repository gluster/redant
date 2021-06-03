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

    def is_shared_volume_mounted(self, node: str) -> bool:
        """
        Checks if shared storage volume is mounted

        Args:
            node (str) : Node on which command is to be executed

        Returns:
            bool : True if successfully disabled shared storage.
                   False otherwise.
        """
        timeout = 20
        counter = 0
        path = "/run/gluster/shared_storage"
        while counter < timeout:
            ret = self.execute_abstract_op_node("df -h", node, False)
            if path in " ".join(ret['msg']):
                self.logger.info("Shared storage is mounted")
                return True

            sleep(2)
            counter += 2

        self.logger.info("Shared storage not mounted")
        return False

    def check_gluster_shared_volume(self, node: str,
                                    present: bool = True) -> bool:
        """
        Check gluster shared volume present or absent.

        Args:
            node (str) : Node on which command is to be executed
            present (bool) : True if you want to check presence
                             False if you want to check absence.

        Returns:
            bool : True if successfully disabled shared storage.
                   False otherwise.
        """
        timeout = 20
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
