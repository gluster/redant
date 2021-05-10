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

    def add_brick(self, node: str, volname: str, 
                 server_list:list, conf_hash: dict, 
                  brick_root: list, force: bool = False):
        """
        This function adds bricks to the volume volname. 

        Args:

            node (str): The node on which the command is to be run.
            volname (str): The volume in which the brick has to be added.
            server_list (list): List of servers provided.
            conf_hash (dict): Config hash providing parameters for adding bricks.
            brick_root (list): List of brick root paths
            force (bool): If set to True will add force in the command being executed.
        

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

        if 'replica_count' in conf_hash:
            mul_fac = conf_hash["replica_count"]

            # if "arbiter_count" in conf_hash:
            #     mul_fac += conf_hash["arbiter_count"]
            
            if "dist_count" in conf_hash:
                mul_fac *= conf_hash["dist_count"]

        elif "dist_count" in conf_hash:
            mul_fac = conf_hash["dist_count"]

        server_val = ""
        if len(server_list) > mul_fac:
            server_val = server_list[mul_fac]
        else:
            server_val = server_list[(mul_fac%len(server_list))]
        
        brick_path_val = f"{brick_root[server_val]}/{volname}-{mul_fac}"

        if server_val not in self.volds[volname]["brickdata"].keys():
            self.volds[volname]["brickdata"][server_val] = []

        self.volds[volname]["brickdata"][server_val].append(brick_path_val)

        brick_cmd = f"{server_val}:{brick_path_val}"

        
        if "replica_count" in conf_hash:
            replica = conf_hash['replica_count']+1
            conf_hash['replica_count'] = replica
            cmd = (f"gluster vol add-brick "
                   f"{volname} replica {replica} "
                   f"{brick_cmd} --xml")

        elif "dist_count" in conf_hash:
            conf_hash['dist_count'] += 1
            cmd = (f"gluster vol add-brick "
                   f"{volname} {brick_cmd} --xml")
        if force:
            cmd = f"{cmd} force"

        ret = self.execute_abstract_op_node(node=node, cmd=cmd)

        return ret

    def remove_brick(self, node: str, volname: str, conf_hash: dict, 
                    server_list:list, brick_root: list, option: str):
        """
        This function removes a brick from the volume volname

        Args:

            node (str): Node on which the command has to be executed.
            volname (str): The volume from which brick(s) have to be removed.
            conf_has (dict):Config hash providing parameters for
                deleting bricks
            brick_root (list): The list of brick root paths
            option (str): Remove brick options: <start|stop|status|commit|force>
  
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

        if "replica_count" in conf_hash:
            mul_fac = conf_hash['replica_count']
        
            if "dist_count" in conf_hash:
                mul_fac *= conf_hash['dist_count']

        elif "dist_count" in conf_has:
            mul_fac = conf_has['dist_count']
        
        server_val = ""

        if len(server_list) > mul_fac:
            server_val = server_list[mul_fac-1]

        else:
            server_val = server_list[(mul_fac%len(server_list))-1]

        brick_path_val = f"{brick_root[server_val]}/{volname}-{mul_fac}"

        brick_cmd = f"{server_val}:{brick_path_val}"

        if "replica_count" in conf_hash:
            replica = conf_hash['replica_count']-1
            conf_hash['replica_count'] = replica
            cmd = (f"gluster vol remove-brick "
                   f"{volname} replica {replica} "
                   f"{brick_cmd} --xml")

        elif "dist_count" in conf_hash:
            conf_hash['dist_count'] -= 1
            cmd = (f"gluster vol remove-brick "
                   f"{volname} {brick_cmd} --xml")
        
        ret = self.execute_abstract_op_node(node=node, cmd=cmd)

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
        cmd = (f"gluster volume replace-brick "
               f"{volname} {src_brick} {dest_brick} "
               f"commit force --xml")

        ret = self.execute_abstract_op_node(node=node, cmd=cmd)
    
        return ret

    def reset_brick(self, node: str, volname: str, src_brick: str, option: str, dst_brick=None, force=False):
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