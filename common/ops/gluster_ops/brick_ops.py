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

    def add_brick(self, node: str, volname: str, force: bool = False, **kwargs):
        """
        This function adds bricks specified in the list (bricks_list)
        in the volume.

        Args:

            node(str): The node on which the command is to be run.
            volname(str): The volume in which the brick has to be added.

        Kwargs:

            force (bool): If this option is set to True, then add brick command
            will get executed with force option. If it is set to False,
            then add brick command will get executed without force option

            **kwargs
                The keys, values in kwargs are:
                    - replica_count : (int)|None
                    - arbiter_count : (int)|None
        Returns:
            ret: A dictionary consisting
                    - Flag : Flag to check if connection failed
                    - msg : message
                    - error_msg: error message
                    - error_code: error code returned
                    - cmd : command that got executed
                    - node : node on which the command got executed
        """
        replica_count = arbiter_count = None

        if 'replica_count' in kwargs:
            replica_count = int(kwargs['replica_count'])

        if 'arbiter_count' in kwargs:
            arbiter_count = int(kwargs['arbiter_count'])

        replica = arbiter = ''

        if replica_count is not None:
            replica = f'replica {replica_count}'

            if arbiter_count is not None:
                arbiter = f'arbiter {arbiter_count}'

        force_value = ''

        if force:
            force_value = 'force'

        bricks_list = self.volds[volname]["brickdata"][node]
        cmd = (f"gluster volume add-brick "
               f"{volname} {replica} {arbiter} "
               f"{' '.join(bricks_list)} {force_value} --xml")

        ret = self.execute_abstract_op_node(node=node, cmd=cmd)

        return ret

    def remove_brick(self, node: str, volname: str,
                     option: str, **kwargs):
        """
        This function removes the bricks
        specified in the bricks_list
        from the volume.

        Args:

            node (str): Node on which the command has to be executed.
            volname (str): The volume from which brick(s) have to be removed.
            option (str): Remove brick options: <start|stop|status|commit|force>
    Kwargs:

        **kwargs
            The keys, values in kwargs are:
                - replica_count : (int)|None
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

        replica_count = None
        replica = ''

        if 'replica_count' in kwargs:
            replica_count = int(kwargs['replica_count'])

        if replica_count is not None:
            replica = f'replica {replica_count}'

        bricks_list = self.volds[volname]["brickdata"][node]

        cmd = (f"gluster volume remove-brick "
               f"{volname} {replica} {' '.join(bricks_list)} "
               f"{option} --xml")

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