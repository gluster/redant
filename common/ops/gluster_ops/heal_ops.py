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
        specified volume.

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

    def get_heal_info(self, node: str, volname: str):
        """
        From the xml output of heal info command get the heal info data.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume

        Returns:
            NoneType: None if parse errors.
            list: list of dictionaries. Each element in the list is the
                heal_info data per brick.
        """
        cmd = f"gluster volume heal {volname} info --xml"
        ret = self.execute_abstract_op_node(cmd, node)
        if ret['msg']['opRet'] != '0':
            self.logger.error("Failed to get the heal info xml output for"
                              f" the volume {volname}.Hence failed to get"
                              " the heal info summary.")
            return None

        heal_info_data = []
        for brick in ret['msg']['healInfo']['bricks']['brick']:
            brick_heal_info = {}
            brick_files_to_heal = []
            file_to_heal_exist = False

            for element in brick:
                if element == 'file':
                    file_to_heal_exist = True
                    file_info = {}
                    file_info[element['gfid']] = brick[element]
                    brick_files_to_heal.append(file_info)
                else:
                    brick_heal_info[element] = brick[element]
            if file_to_heal_exist:
                brick_heal_info['file'] = brick_files_to_heal
            heal_info_data.append(brick_heal_info)
        return heal_info_data

    def is_heal_complete(self, node: str, volname: str) -> bool:
        """
        Verifies there are no pending heals on the volume.
        The 'number of entries' in the output of heal info
        for all the bricks should be 0 for heal to be completed.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume

        Returns:
            bool: True if heal is complete. False otherwise
        """
        heal_info_data = self.get_heal_info(node, volname)
        if heal_info_data is None:
            self.logger.error("Unable to identify whether heal is"
                              f" successfull or not on volume {volname}")
            return False

        for brick_heal_info_data in heal_info_data:
            if brick_heal_info_data["numberOfEntries"] != '0':
                self.logger.error("Heal is not complete on some of the bricks"
                                  f" for the volume {volname}")
                return False

        self.logger.info("Heal is complete for all the bricks"
                         f" on the volume {volname}")
        return True

    def monitor_heal_completion(self, node: str, volname: str,
                                timeout_period=1200, bricks=None,
                                interval_check=120) -> bool:
        """
        Monitors heal completion by looking into .glusterfs/indices/xattrop
        directory of every brick for certain time. When there are no entries
        in all the brick directories then heal is successful.
        Otherwise heal is pending on the volume.

        Args:
            node : Node on which commands are executed
            volname : Name of the volume
            timeout_period : time until which the heal monitoring to be done.
                             Default: 1200 i.e 20 minutes.
            bricks : list of bricks to monitor heal, if not provided
                    heal will be monitored on all bricks of volume
            interval_check : Time in seconds, for every given interval checks
                            the heal info, defaults to 120.

        Returns:
            bool: True if heal is complete within timeout_period.
            False otherwise
        """
        if timeout_period != 0:
            heal_monitor_timeout = timeout_period

        time_counter = heal_monitor_timeout
        self.logger.info("Heal monitor timeout is : ",
                         f"{(heal_monitor_timeout / 60)} minutes")

        # Get all bricks
        bricks_list = bricks or self.get_all_bricks(volname, node)
        if bricks_list is None:
            self.logger.error("Unable to get the bricks list. Hence"
                              "unable to verify whether self-heal-daemon "
                              "process is running or not "
                              f"on the volume {volname}")

            return False

        while time_counter > 0:
            heal_complete = True

            for brick in bricks_list:
                brick_node, brick_path = brick.split(":")
                cmd = (f"ls -1 {brick_path}/.glusterfs/indices/xattrop/ | "
                       "grep -ve \"xattrop-\" | wc -l")
                ret = self.execute_abstract_op_node(cmd, brick_node)
                out = int((ret['msg'][0]).rstrip("\n"))
                if out != 0:
                    heal_complete = False
            if heal_complete:
                break
            sleep(interval_check)
            time_counter = time_counter - interval_check

        if heal_complete and bricks:
            # In EC volumes, check heal completion only on online bricks
            # and `gluster volume heal info` fails for an offline brick
            return True

        if heal_complete and not bricks:
            heal_completion_status = self.is_heal_complete(node, volname)

            if heal_completion_status:
                self.logger.info("Heal has successfully completed"
                                 f" on volume {volname}")

                return True

        self.logger.info(f"Heal has not yet completed on volume {volname}")

        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            cmd = f"ls -1 {brick_path}/.glusterfs/indices/xattrop/ "
            self.execute_abstract_op_node(cmd, brick_node)
        return False
