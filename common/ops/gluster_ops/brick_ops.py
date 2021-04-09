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

    def add_brick(self, node: str, volname: str, bricks_list: list, force: bool = False, **kwargs):
        """
        This function adds bricks specified in the list (bricks_list)
        in the volume.

        Args:

            node(str): The node on which the command is to be run.
            volname(str): The volume in which the brick has to be added.
            bricks_list(list) : The list of bricks.

        Kwargs:

            force (bool): If this option is set to True, then add brick command
            will get executed with force option. If it is set to False,
            then add brick command will get executed without force option

            **kwargs
                The keys, values in kwargs are:
                    - replica_count : (int)|None
                    - arbiter_count : (int)|None
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

        cmd = (f"gluster volume add-brick "
               f"{volname} {replica} {arbiter} "
               f"{' '.join(bricks_list)} {force_value} --xml")

        self.logger.info(f"Running {cmd} on {node}")
        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret["error_code"]) != 0:
            self.logger.error(ret["error_msg"])
            raise Exception(ret["error_msg"])

        self.logger.info(f"Successfully ran {cmd} on {node}")

    def remove_brick(self, node: str, volname: str, bricks_list: list,
                     option: str, **kwargs):
        """
        This function removes the bricks
        specified in the bricks_list
        from the volume.

        Args:

            node (str): Node on which the command has to be executed.
            volname (str): The volume from which brick(s) have to be removed.
            bricks_list (list): List of bricks to be removed
            option (str): Remove brick options: <start|stop|status|commit|force>
    Kwargs:

        **kwargs
            The keys, values in kwargs are:
                - replica_count : (int)|None

        """
        option = option + ' --mode=script'

        replica_count = None
        replica = ''

        if 'replica_count' in kwargs:
            replica_count = int(kwargs['replica_count'])

        if replica_count is not None:
            replica = f'replica {replica_count}'

        cmd = (f"gluster volume remove-brick "
               f"{volname} {replica} {' '.join(bricks_list)} "
               f"{option} --xml")
        self.logger.info(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['msg']['opRet']) != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

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
        
        """
        cmd = (f"gluster volume replace-brick "
               f"{volname} {src_brick} {dest_brick} "
               f"commit force --xml")

        self.logger.info(f"Running {cmd} on node {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['msg']['opRet']) != 0:
            self.logger.error(ret['msg']['opErrstr'])
            raise Exception(ret['msg']['opErrstr'])

        self.logger.info(f"Successfully ran {cmd} on {node}")
    