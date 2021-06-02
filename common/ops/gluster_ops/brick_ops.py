"""
Brick ops module deals with the functions related to brick related operations.
"""

from time import sleep
import random
from common.ops.abstract_ops import AbstractOps


class BrickOps(AbstractOps):
    """
    Class which is responsible for methods for brick related operations.
    """

    def add_brick(self, volname: str, brick_str: str, node: str,
                  force: bool = False, replica_count: int = None,
                  arbiter_count: int = None) -> dict:
        """
        # TODO: Function has to designed for dispersed, distributed-dispersed,
                arbiter and distributed-arbiter.
        This function adds bricks to the volume volname.

        Args:

            volname (str): The volume in which the brick has to be added.
            brick_str (str): string of brick command.
            node (str): The node on which the command is to be run.
            force (bool): If set to True will add force in the command
                          being executed.
            replica_count (int): Updated replica count
            arbiter_count (int): Updated arbiter count

        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        """
        replica = arbiter = ''
        if replica_count is not None:
            replica = (f"replica {replica_count}")
            if arbiter_count is not None:
                arbiter = (f"arbiter {arbiter_count}")

        cmd = (f"gluster vol add-brick {volname} {replica} {arbiter}"
               f" {brick_str} --mode=script --xml")

        # Defaulting the mode to be force due to CI.
        force = True
        if force:
            cmd = (f"{cmd} force")
        ret = self.execute_abstract_op_node(cmd, node)

        server_brick = {}
        for brickd in brick_str.split(' '):
            node, bpath = brickd.split(':')
            if node not in server_brick:
                server_brick[node] = []
            server_brick[node].append(bpath)
        self.es.add_bricks_to_brickdata(volname, server_brick)

        return ret

    def remove_brick(self, node: str, volname: str, brick_list: list,
                     option: str, replica_count: int = None) -> dict:
        """
        This function removes the given list of bricks from the volume.

        Args:

            node (str): Node on which the command has to be executed.
            volname (str): The volume from which brick(s) have to be removed.
            brick_list (list): The list of bricks to be removed
            option (str): Remove brick options:
                          <start|stop|status|commit|force>
            replica_count (int): Optional parameter with default value as None.

        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        NOTE: For now the option change is to be handled by the user. The count
        values have to be modified after remove brick is a success. Also,
        a TODO is to check the commit force option and its incorporation in
        this function.
        """
        replica = ''
        if replica_count is not None:
            replica = (f"replica {replica_count}")

        brick_cmd = " ".join(brick_list)
        cmd = (f"gluster vol remove-brick {volname} {replica} {brick_cmd}"
               f" {option} --mode=script --xml")

        ret = self.execute_abstract_op_node(cmd, node)
        if option in ['commit', 'force']:
            server_brick = {}
            for brickd in brick_list:
                node, bpath = brickd.split(':')
                if node not in server_brick:
                    server_brick[node] = []
                server_brick[node].append(bpath)
            self.es.remove_bricks_from_brickdata(volname, server_brick)

        return ret

    def replace_brick(self, node: str, volname: str,
                      src_brick: str, dest_brick: str,
                      excep: bool = True) -> dict:
        """
        This function replaces one brick(source brick)
        with the another brick(destination brick) on the volume.

        Args:
            node (str): The node on which the command has to be executed
            volname (str): The volume on which the bricks have to be replaced.
            src_brick (str) : The source brick name
            dest_brick (str) : The destination brick name
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
        # TODO:server val to modify the new brick path
        cmd = (f"gluster volume replace-brick "
               f"{volname} {src_brick} {dest_brick} "
               f"commit force --xml")

        ret = self.execute_abstract_op_node(cmd, node, excep)

        return ret

    def replace_brick_from_volume(self, volname: str, node: str,
                                  servers: list, src_brick: str = None,
                                  dst_brick: str = None,
                                  delete_brick: bool = True) -> bool:
        """
        Replace faulty brick from a volume

        Args:
            volname (str): Volume in which the brick has to be replaced
            node (str): Node on which command has to be executed
            server_list (list): List of servers in the cluster

        Optional:
            src_brick (str): Brick to be replaced
            dst_brick (str): New brick which will replace the old one
            delete_brick (bool): True, if the old brick should be deleted
                                 otherwise False. (Default is True)

        Returns:
            bool: True if the replace brick operation was successful,
                  False if the operation failed.
        """
        if not isinstance(servers, list):
            servers = [servers]

        # Check if volume exists
        if not self.es.does_volume_exists(volname):
            self.logger.error(f"Volume {volname} does not exist")
            return False

        # TODO: Update when we have get_subvols function
        # subvols_info = self.get_subvols(volname, node)

        if not dst_brick:
            _, dst_brick = self.form_brick_cmd(servers, self.brick_roots,
                                               self.vol_name, 1)

            if not dst_brick:
                self.logger.error("Failed to get a new brick to replace")

        # TODO: Update when we have get_subvols function
        # if not src_brick:
        #     # Randomly select a brick to replace
        #     subvols_list = subvols_info['volume_subvols']
        #     src_brick = (choice(choice(subvols_list)))

        # Bring src brick offline
        if not self.bring_bricks_offline(volname, src_brick):
            self.logger.error("Failed to bring source brick offline")

        # Wait for src brick to go offline
        if not self.wait_for_bricks_to_go_offline(volname, src_brick):
            self.logger.error("Brick is still not offline for replace brick"
                              " operation")
            return False

        # Check volume status before replace brick operation
        ret = self.get_volume_status(volname, node)
        if ret is None:
            self.logger.error("Failed to get volume status")
            return False

        # Perform replace brick
        ret = self.replace_brick(node, volname, src_brick, dst_brick, False)
        if ret['msg']['opRet'] != 0:
            self.logger.error(f"Failed to replace brick: {src_brick}")

        # Delete old brick
        if delete_brick:
            brick_node, brick_path = src_brick.split(':')
            brick_dict_remove = {brick_node: [brick_path]}
            self.es.add_data_to_cleands(brick_dict_remove)

        return True

    def reset_brick(self, node: str, volname: str, src_brick: str,
                    option: str, dst_brick=None, force=False):
        """
        Resets brick in a volume

        Args:
            node (str) : Node on which the command has to be executed
            volname (str) : Name of the volume on which the brick
                            has to be reset
            src_brick (str) : Name of the source brick
            dst_brick (str) : Name of the destination brick
            option (str) : Options for reset brick : start | commit | force

        Kwargs:
            force (bool) : If this option is set to True,
                then reset brick will get executed with force option

        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        """

        if option == "start":
            cmd = f"gluster vol reset-brick {volname} {src_brick} start"

        elif option == "commit":
            if dst_brick is None:
                dst_brick = src_brick

            cmd = f"gluster vol reset-brick {src_brick} {dst_brick} {option}"

            if force:
                cmd = f"{cmd} force"

        ret = self.execute_abstract_op_node(cmd=cmd, node=node)

        return ret

    def form_brick_cmd(self, server_list: list, brick_root: list,
                       volname: str, mul_fac: int, add_flag: bool = False):
        """
        # TODO: Function has to designed for dispersed, distributed-dispersed,
                arbiter and distributed-arbiter.
        This function helps in forming
        the brick command

        Args:
            server_list (list): List of servers
            brick_root (list) : List of brick roots
            volname (str) : Name of the volume
            mul_fac (int) : Stores the number of bricks
                            needed to form the brick command
            add_flag (bool): Indicates whether the command creation is for
                             add/replace brick scenario or volume creation.
                             Optional parameter which by default is False.

        Returns:

        A tuple containing:
            brick_dict (dict) : Dictionary of servers and their
                                corresponding brick roots
            brick_cmd (str) : Command which contains the brick
                              paths.
        """
        if not isinstance(server_list, list):
            server_list = [server_list]

        brick_dict = {}
        brick_cmd = ""
        server_iter = 0

        iter_add = 0
        if add_flag:
            iter_add = len(self.get_all_bricks(volname, server_list[0]))

        for iteration in range(mul_fac):
            if server_iter == len(server_list):
                server_iter = 0
            server_val = server_list[server_iter]
            if server_val not in brick_dict.keys():
                brick_dict[server_val] = []
            brick_path_val = (
                f"{brick_root[server_list[server_iter]]}/{volname}-"
                f"{iteration+iter_add}")
            brick_dict[server_val].append(brick_path_val)
            brick_cmd = (f"{brick_cmd} {server_val}:{brick_path_val}")
            server_iter += 1

        brick_cmd = brick_cmd.lstrip(" ")

        return (brick_dict, brick_cmd)

    def cleanup_brick_dirs(self):
        """
        This function requests for the cleands and clears the brick dirs which
        have been populated in it.
        """
        cleands_val = list(self.es.get_cleands_data().items())
        for (node, b_dir_l) in cleands_val:
            for b_dir in b_dir_l:
                self.execute_abstract_op_node(f"rm -rf {b_dir}", node)
                self.es.remove_val_from_cleands(node, b_dir)

    def are_bricks_offline(self, volname: str,
                           bricks_list: list, node: str,
                           strict: bool = True) -> bool:
        """
        This function checks if the given list of
        bricks are offline.

        Args:
            volname (str) : Volume name
            bricks_list (list) : list of bricks to check
            node (str) : the node on which comparison has to be done
            strict (bool) : To check strictly if all bricks are offline
        Returns:
            boolean value: True, if bricks are offline
                           False if online
        """
        vol_status = self.get_volume_status(volname, node)

        vol_status_brick_list = []
        for n in vol_status[volname]['node']:
            if int(n['status']) == 1:
                brick = f"{n['hostname']}:{n['path']}"
                vol_status_brick_list.append(brick)

        online_brick_list = []
        ret = True

        for brick in bricks_list:
            if strict and brick in vol_status_brick_list:
                online_brick_list.append(brick)
                self.logger.error(f"Brick: {brick} is not offline")
                ret = False
            elif brick in vol_status_brick_list:
                self.logger.error(f"Brick: {brick} is not offline")
                return False

        if not ret:
            self.logger.error(f"Some of the bricks are not "
                              f"offline: {online_brick_list}")
            return ret

        self.logger.info(f"All bricks are offline: {bricks_list}")
        return ret

    def are_bricks_online(self, volname: str,
                          bricks_list: list, node: str,
                          strict: bool = True) -> bool:
        """
        This function checks if the given list of
        bricks are online.

        Args:
            volname (str) : Volume name
            bricks_list (list) : list of bricks to check
            node (str) : the node on which comparison has to be done
            strict (bool) : To check strictly if all bricks are offline
        Returns:
            boolean value: True, if bricks are offline
                           False if online
        """
        vol_status = self.get_volume_status(volname, node)

        vol_status_brick_list = []
        for brick in vol_status[volname]['node']:
            if int(brick['status']) == 1:
                brick_path = f"{brick['hostname']}:{brick['path']}"
                vol_status_brick_list.append(brick_path)

        offline_brick_list = []
        ret = True

        for brick in bricks_list:
            if strict and brick not in vol_status_brick_list:
                offline_brick_list.append(brick)
                self.logger.error(f"Brick: {brick} is not online")
                ret = False
            elif brick not in vol_status_brick_list:
                self.logger.error(f"Brick: {brick} is not online")
                return False

        if not ret:
            self.logger.error(f"Some of the bricks are "
                              f"not online: {offline_brick_list}")
            return ret

        self.logger.info(f"All bricks are online: {bricks_list}")
        return ret

    def check_if_bricks_list_changed(self,
                                     bricks_list: list,
                                     volname: str,
                                     node: str) -> bool:
        """
        Checks if the brick list changed.

        Args:
            bricks_list: list of bricks
            volname: Name of volume
            node: Node on which to execute vol info

        Returns:
        bool: True is list changed
              else False
        """
        vol_info = self.get_volume_info(node, volname)

        vol_info_brick_list = []
        for n in vol_info[volname]['bricks']:
            vol_info_brick_list.append(n['name'])

        if len(vol_info_brick_list) == len(bricks_list):
            for each in bricks_list:
                if each not in vol_info_brick_list:
                    return True
            return False
        return True

    def get_all_bricks(self, volname: str, node: str) -> list:
        """
        Get list of all the bricks of the specified volume.

        Args:
            volname (str): Name of the volume
            node (str): Node on which command has to be executed

        Returns:
            list: List of all the bricks of the volume on Success.
            NoneType: None on failure.
        """

        vol_info = self.get_volume_info(node, volname)
        if vol_info is None:
            self.logger.error(f"Unable to get "
                              f"the volinfo of {volname}.")
            return None

        # Get bricks from a volume
        all_bricks = []
        if 'bricks' in vol_info[volname]:
            for brick in vol_info[volname]['bricks']:
                if 'name' in brick:
                    all_bricks.append(brick['name'])
                else:
                    self.logger.error(f"Brick {brick} doesn't have the "
                                      f"key 'name' for the volume {volname}")
                    return None
            return all_bricks
        self.logger.error(f"Bricks not found in the volume {volname}")
        return None

    def get_online_bricks_list(self, volname: str, node: str) -> list:
        """
        Get list of bricks which are online.

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.

        Returns:
            list : List of bricks in the volume which are online.
            NoneType: None on failure in getting volume status
        """
        online_bricks_list = []
        try:
            volume_status = self.get_volume_status(volname, node)
        except Exception as error:
            self.logger.info(f"Volume status failed: {error}")
            return None

        if not volume_status:
            self.logger.error(f"Unable to get online bricks_list "
                              f"for the volume {volname}")
            return None
        all_bricks = self.get_all_bricks(volname, node)

        volume_status = volume_status[volname]
        if 'node' in volume_status:
            for brick in volume_status['node']:
                if 'status' in brick:
                    if int(brick['status']) == 1:
                        cmp_brick_path = (f"{brick['hostname']}:"
                                          f"{brick['path']}")
                        if cmp_brick_path in all_bricks:
                            online_bricks_list.append(cmp_brick_path)
                else:
                    self.logger.error(f"Key 'status' not in brick: {brick}")
                    return None

            return online_bricks_list
        self.logger.error(f"Key 'node' not in volume status of {volname}")
        return None

    def get_offline_bricks_list(self, volname: str, node: str) -> list:
        """
        Get list of bricks which are offline.

        Args:
            volname (str): Name of the volume.
            node (str): Node on which commands will be executed.

        Returns:
            list : List of bricks in the volume which are offline.
            NoneType: None on failure in getting volume status
        """
        offline_bricks_list = []
        all_bricks = self.get_all_bricks(volname, node)
        try:
            volume_status = self.get_volume_status(volname, node)
        except Exception as error:
            self.logger.info(f"Volume status failed: {error}")
            return all_bricks

        if not volume_status:
            self.logger.error(f"Unable to get offline bricks_list "
                              f"for the volume {volname}")
            return None

        volume_status = volume_status[volname]
        if 'node' in volume_status:
            for brick in volume_status['node']:
                if 'status' in brick:
                    cmp_brick_path = (f"{brick['hostname']}:"
                                      f"{brick['path']}")
                    if int(brick['status']) != 1:
                        if cmp_brick_path in all_bricks:
                            offline_bricks_list.append(cmp_brick_path)
                    elif int(brick['status']) == 1:
                        if cmp_brick_path in all_bricks:
                            all_bricks.remove(cmp_brick_path)
                else:
                    self.logger.error(f"Key 'status' not in brick: {brick}")
                    return None

            for brick in all_bricks:
                if brick not in offline_bricks_list:
                    offline_bricks_list.append(brick)

            return offline_bricks_list
        self.logger.error(f"Key 'node' not in volume status of {volname}")
        return None

    def wait_for_bricks_to_go_offline(self, volname: str, brick_list: list,
                                      timeout: int = 100) -> bool:
        """
        Function to wait till the given set of bricks in brick list go offline.

        Args:
            volname (str): Name of the volume whose bricks are to be noticed.
            brick_list (list): List of bricks which are to be brought down.
            timeout (int): Optional parameter with defailt value 100. The
            function waits for these many secondsat max till bricks go offline.

        Returns:
            True if the bricks go offline or False.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        nd_list = []
        for brickd in brick_list:
            if brickd.split(':')[0] not in nd_list:
                nd_list.append(brickd.split(':')[0])
        itr = 0
        while itr < timeout:
            random_node = random.choice(nd_list)
            offline_brick_list = self.get_offline_bricks_list(volname,
                                                              random_node)
            if offline_brick_list is not None and\
                    set(brick_list).issubset(set(offline_brick_list)):
                return True
            itr += 5
            sleep(5)
        self.logger.error(f"Current offline brick list : {offline_brick_list}"
                          " Compared to expected offline brick list :"
                          f" {brick_list}")
        return False

    def wait_for_bricks_to_come_online(self, volname: str, server_list: list,
                                       brick_list: list,
                                       timeout: int = 100) -> bool:
        """
        Function to wait till the given set of bricks in brick list come
        online.

        Args:
            volname (str): Name of the volume whose bricks are to be brought
                           online.
            server_list (list): A list of servers which are hosting the volume.
            brick_list (list): List of bricks which are to be brought up.
            timeout (int): Optional parameter with defailt value 100. The
                           function waits for these many seconds at max till
                           bricks come online.

        Returns:
            True if the bricks come online or False.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        itr = 0
        while itr < timeout:
            random_node = random.choice(server_list)
            online_brick_list = self.get_online_bricks_list(volname,
                                                            random_node)
            if online_brick_list is not None and\
                    set(brick_list).issubset(set(online_brick_list)):
                return True
            itr += 5
            sleep(5)

        self.logger.error(f"Current online brick list : {online_brick_list}"
                          " Compared to expected online brick list :"
                          f" {brick_list}")
        return False

    # TODO Brick mux logic inclusion.
    def bring_bricks_offline(self, volname: str, brick_list: list,
                             timeout: int = 100) -> bool:
        """
        Function to bring the given set of bricks offline.

        Args:
            volname (str): Name of the volume whose bricks are to be brought
                           down.
            brick_list (list): List of bricks which are to be brought down.
            timeout (int): Optional parameter with defailt value 100. The
            function waits for these many secondsat max till bricks go offline.

        Returns:
            True if the bricks are brought offline or False.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        self.logger.info(f"Getting {brick_list} offline.")
        nd_list = []
        for brick in brick_list:
            nd, path = brick.split(":")
            if nd not in nd_list:
                nd_list.append(nd)
            path = path.replace("/", "-")
            cmd = (f"pid=`ps -ef | grep -ve 'grep' | grep -e '{nd}{path}.pid' "
                   " | awk '{print $2}'` && kill -15 $pid || kill -9 $pid")
            ret = self.execute_abstract_op_node(cmd, nd, False)
            if ret['error_code'] != 0:
                self.logger.error(f"Failed to bring {brick_list} offline."
                                  f" As {cmd} failed on {nd}")
                return False

        # Wait till the said bricks come offline.
        return self.wait_for_bricks_to_go_offline(volname, brick_list, timeout)

    # TODO Brick mux logic inclusion.
    def bring_bricks_online(self, volname: str, server_list: list,
                            brick_list: list, disrup_method: bool = False,
                            timeout: int = 100) -> bool:
        """
        Function to bring the bricks belonging to a volume online. One can
        either use a disruptive mode to achive this or a non-disruptive way.

        Args:
            volname (str): Name of the volume whose bricks have to be brought
                           online.
            server_list (list): Nodes of the cluster.
            brick_list (list): The bricks which are offline.
            disrup_method (bool): Whether to use a disruptive way of starting
                                  the bricks using glusterd start or a non
                                  disruptive way of starting the bricks using
                                  volume start with force option.
            timeout (int): The timout till which we will check whether the
                           bricks have come online.

        Returns:
            True if the bricks are online or False.
        """
        if not isinstance(brick_list, list):
            brick_list = [brick_list]

        if not disrup_method:
            self.logger.info(f"Getting bricks {brick_list} online by forced"
                             f" volume start of {volname}")
            self.volume_start(volname, random.choice(server_list), True)
        else:
            self.logger.info(f"Getting bricks {brick_list} online by "
                             " glusterd restart in respective nodes.")
            node_list = []
            for bdata in brick_list:
                if bdata.split(':')[0] not in node_list:
                    node_list.append(bdata.split(':')[0])
            for nd in node_list:
                self.restart_glusterd(nd)
                self.wait_for_glusterd_to_start(nd)

        self.wait_till_all_peers_connected(server_list)

        # Wait till all said bricks are online.
        return self.wait_for_bricks_to_come_online(volname, server_list,
                                                   brick_list, timeout)

    def get_brick_processes_count(self, node: str) -> int:
        """
        Get the brick process count for a given node.

        Args:
            node (str): Node on which brick process has to be counted.

        Returns:
            int: Number of brick processes running on the node.
            None: If the command fails to execute.
        """
        ret = self.execute_abstract_op_node("pgrep -c glusterfsd", node,
                                            False)
        if ret['error_code'] == 0:
            count_of_proc = int(ret['msg'][0].rstrip('\n'))
            return count_of_proc
        else:
            return None
