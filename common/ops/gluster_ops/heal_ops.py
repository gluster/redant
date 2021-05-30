"""
Heal ops module deals with the functions related to heal related operations.
"""

from time import sleep


class HealOps:
    """
    Class which is responsible for methods for heal related operations.
    """

    def wait_for_self_heal_daemons_to_be_online(self, volname: str, node: str,
                                                timeout: int = 300) -> bool:
        """
        Waits for the volume self-heal-daemons to be online until timeout

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.

        Optional:
            timeout (int): timeout value in seconds to wait for
                           self-heal-daemons to be online.

        Returns:
            bool : True if all self-heal-daemons are online within timeout,
                   False otherwise
        """
        # Return True if the volume is pure distribute
        if self.is_distribute_volume(volname):
            self.logger.info(f"Volume {volname} is a distribute volume. "
                             "Hence not waiting for self-heal daemons "
                             "to be online")
            return True

        counter = 0
        flag = 0
        while counter < timeout:
            status = self.are_all_self_heal_daemons_online(volname, node)
            if status:
                flag = 1
                break
            if not status:
                sleep(10)
                counter = counter + 10

        if not flag:
            self.logger.error(f"All self-heal-daemons of the volume {volname}"
                              f" are not online even after {timeout//60}"
                              " minutes")
            return False
        else:
            self.logger.info(f"All self-heal-daemons of the volume {volname}"
                             " are online")
        return True

    def are_all_self_heal_daemons_online(self, volname: str,
                                         node: str) -> bool:
        """
        Verifies whether all the self-heal-daemons are online for the
        specified
        volume.

        Args:
            volname (str): volume name
            node (str): Node on which cmd has to be executed.

        Returns:
            bool : True if all the self-heal-daemons are online for the volume.
                   False otherwise.
            NoneType: None if unable to get the volume status
        """
        if self.is_distribute_volume(volname):
            self.logger.info(f"Volume {volname} is a distribute volume. "
                             "Hence not waiting for self-heal daemons "
                             "to be online")
            return True

        service = 'shd'
        failure_msg = ("Verifying all self-heal-daemons are online failed for "
                       f"volume {volname}")
        # Get volume status
        vol_status = self.get_volume_status(volname, node, service)
        if vol_status is None:
            self.logger.error(failure_msg)
            return None

        # Get all nodes from pool list
        all_nodes = self.nodes_from_pool_list(node)
        if not all_nodes:
            self.logger.error(failure_msg)
            return False

        online_status = True
        if 'node' in vol_status[volname]:
            for brick in vol_status[volname]['node']:
                if brick['hostname'] == "Self-heal Daemon":
                    if brick['status'] != '1':
                        online_status = False
                        break

        if online_status:
            self.logger.info("All self-heal Daemons are online")
            return True
        else:
            self.logger.error("Some of the self-heal Daemons are offline")
            return False
