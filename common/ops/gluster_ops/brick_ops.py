"""
This part deals with the ops related to the bricks

class - BrickOps
"""


class BrickOps:
    """
    It provides the following functionalities:

    add_brick
    remove_brick
    replace_brick
    reset_brick
    """

    def add_brick(self, volname: str, node: str,
                  conf_hash: dict, server_list: list,
                  brick_root: list, force: bool = False):
        """
        This function adds bricks to the volume volname.

        Args:

            volname (str): The volume in which the brick has to be added.
            node (str): The node on which the command is to be run.
            conf_hash (dict): Config hash providing parameters for adding
            bricks.
            server_list (list): List of servers provided.
            brick_root (list): List of brick root paths
            force (bool): If set to True will add force in the command
                          being executed.


        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        """

        brick_cmd = ""
        server_iter = 0
        mul_fac = 0
        cmd = ""
        server_val = ""
        server_iter = 0
        bricks_list = []

        if "replica_count" in conf_hash:
            mul_fac = conf_hash['replica_count']

            if "arbiter_count" in conf_hash:
                mul_fac += conf_hash['arbiter_count']

            if "dist_count" in conf_hash:
                mul_fac *= conf_hash['dist_count']

        elif "dist_count" in conf_hash:
            mul_fac = conf_hash['dist_count']

        if len(server_list) > mul_fac:
            server_iter = mul_fac

        else:
            server_iter = (mul_fac % len(server_list))

        num_bricks = 1

        if "arbiter_count" in conf_hash:
            num_bricks = num_bricks + 2

        if "dist_count" in conf_hash and "replica_count" in conf_hash:
            num_bricks = num_bricks + 2

        server_brick = {}

        for i in range(num_bricks):

            server_val = server_list[server_iter]

            brick_path_val = f"{brick_root[server_val]}/{volname}-{mul_fac+i}"
            if server_val not in server_brick:
                server_brick[server_val] = []
            server_brick[server_val].append(brick_path_val)

            brick_cmd = f"{server_val}:{brick_path_val}"

            bricks_list.append(brick_cmd)
            server_iter = (server_iter + 1) % len(server_list)

        if "replica_count" in conf_hash:
            replica = conf_hash['replica_count'] + 1

            if "arbiter_count" in conf_hash:
                replica += 1
                arbiter = conf_hash['arbiter_count'] + 1

                conf_hash['arbiter_count'] = arbiter
                conf_hash['replica_count'] = replica
                cmd = (f"gluster vol add-brick "
                       f"{volname} replica 3 arbiter 1 "
                       f"{' '.join(bricks_list)} --xml")
            elif "dist_count" in conf_hash:
                conf_hash['dist_count'] += 1
                cmd = (f"gluster vol add-brick "
                       f"{volname} replica 3 "
                       f"{' '.join(bricks_list)} --xml")
            else:
                conf_hash['replica_count'] = replica
                cmd = (f"gluster vol add-brick "
                       f"{volname} replica {replica} "
                       f"{' '.join(bricks_list)} --xml")

        elif "dist_count" in conf_hash:
            conf_hash['dist_count'] += 1
            cmd = (f"gluster vol add-brick "
                   f"{volname} {' '.join(bricks_list)} --xml")
        if force:
            cmd = f"{cmd} force"

        ret = self.execute_abstract_op_node(node=node, cmd=cmd)

        self.es.add_bricks_to_brickdata(volname, server_brick)
        return ret

    def remove_brick(self, node: str, volname: str, conf_hash: dict,
                     server_list: list, brick_root: list, option: str):
        """
        This function removes a brick or set of bricks
        from the volume volname

        Args:

            node (str): Node on which the command has to be executed.
            volname (str): The volume from which brick(s) have to be removed.
            conf_hash (dict):Config hash providing parameters for
                deleting bricks
            brick_root (list): The list of brick root paths
            option (str): Remove brick options:
                          <start|stop|status|commit|force>

        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed

        """
        option = option + ' --mode=script'

        brick_cmd = ""
        server_iter = 0
        mul_fac = 0
        cmd = ""
        server_val = ""
        server_iter = 0
        bricks_list = []

        if "replica_count" in conf_hash:
            mul_fac = conf_hash['replica_count']

            if "arbiter_count" in conf_hash:
                mul_fac += conf_hash['arbiter_count']

            if "dist_count" in conf_hash:
                mul_fac *= conf_hash['dist_count']

        elif "dist_count" in conf_hash:
            mul_fac = conf_hash['dist_count']

        if len(server_list) > mul_fac:
            server_iter = mul_fac - 1

        else:
            server_iter = (mul_fac % len(server_list)) - 1

        num_bricks = 1

        if "arbiter_count" in conf_hash:
            num_bricks = num_bricks + 2

        if "dist_count" in conf_hash and "replica_count" in conf_hash:
            num_bricks = num_bricks + 2

        server_brick = {}
        for i in range(num_bricks):

            server_val = server_list[server_iter]

            brick_path_val = (f"{brick_root[server_val]}"
                              f"/{volname}-{mul_fac-i-1}")

            if server_val not in server_brick:
                server_brick[server_val] = []

            server_brick[server_val].append(brick_path_val)

            brick_cmd = f"{server_val}:{brick_path_val}"

            bricks_list.append(brick_cmd)
            server_iter = (server_iter - 1) % len(server_list)

        if "replica_count" in conf_hash:
            replica = conf_hash['replica_count'] - 1

            if "arbiter_count" in conf_hash:
                conf_hash['replica_count'] = replica
                cmd = (f"gluster vol remove-brick "
                       f"{volname} replica 3 "
                       f"{' '.join(bricks_list)} {option} --xml")
            elif "dist_count" in conf_hash:
                conf_hash['dist_count'] -= 1
                cmd = (f"gluster vol remove-brick "
                       f"{volname} replica {conf_hash['replica_count']} "
                       f"{' '.join(bricks_list)} {option} --xml")
            else:
                conf_hash['replica_count'] = replica
                cmd = (f"gluster vol remove-brick "
                       f"{volname} replica {replica} "
                       f"{' '.join(bricks_list)} {option} --xml")

        elif "dist_count" in conf_hash:
            conf_hash['dist_count'] -= 1
            cmd = (f"gluster vol remove-brick "
                   f"{volname} {' '.join(bricks_list)} {option} --xml")

        ret = self.execute_abstract_op_node(node=node, cmd=cmd)
        self.es.remove_bricks_from_brickdata(volname, server_brick)

        return ret

    def replace_brick(self, node: str, volname: str,
                      src_brick: str, dest_brick: str):
        """
        This function replaces one brick(source brick)
        with the another brick(destination brick) on the volume.

        Args:
            node (str): The node on which the command has to be executed
            volname (str): The volume on which the bricks have to be replaced.
            src_brick (str) : The source brick name
            dest_brick (str) : The destination brick name

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

        ret = self.execute_abstract_op_node(node=node, cmd=cmd)

        return ret

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
                       volname: str, mul_fac: int):
        """
        This function helps in forming
        the brick command

        Args:
            server_list (list): List of servers
            brick_root (list) : List of brick roots
            volname (str) : Name of the volume
            mul_fac (int) : Stores the number of bricks
                            needed to form the brick command

        Returns:

        A tuple containing:
            brick_dict (dict) : Dictionary of servers and their
                                corresponding brick roots
            brick_cmd (str) : Command which contains the brick
                              paths.
        """
        brick_dict = {}
        brick_cmd = ""
        server_iter = 0

        for iteration in range(mul_fac):
            if server_iter == len(server_list):
                server_iter = 0
            server_val = server_list[server_iter]
            if server_val not in brick_dict.keys():
                brick_dict[server_val] = []
            brick_path_val = \
                f"{brick_root[server_list[server_iter]]}/{volname}-{iteration}"
            brick_dict[server_val].append(brick_path_val)
            brick_cmd = (f"{brick_cmd} {server_val}:{brick_path_val}")
            server_iter += 1

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
            if n['status'] == 1:
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

    def get_online_bricks_list(self, volname: str, node: str):
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
        volume_status = self.get_volume_status(volname, node)
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

    def get_offline_bricks_list(self, volname: str, node: str):
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
        volume_status = self.get_volume_status(volname, node)
        if not volume_status:
            self.logger.error(f"Unable to get offline bricks_list "
                              f"for the volume {volname}")
            return None
        all_bricks = self.get_all_bricks(volname, node)

        volume_status = volume_status[volname]
        if 'node' in volume_status:
            for brick in volume_status['node']:
                if 'status' in brick:
                    if int(brick['status']) != 1:
                        cmp_brick_path = (f"{brick['hostname']}:"
                                          f"{brick['path']}")
                        if cmp_brick_path in all_bricks:
                            offline_bricks_list.append(cmp_brick_path)
                else:
                    self.logger.error(f"Key 'status' not in brick: {brick}")
                    return None
            return offline_bricks_list
        self.logger.error(f"Key 'node' not in volume status of {volname}")
        return None
