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
