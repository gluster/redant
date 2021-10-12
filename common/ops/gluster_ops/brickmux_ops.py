"""
Module for gluster brick multiplex operations
"""

from common.ops.abstract_ops import AbstractOps


class BrickMuxOps(AbstractOps):
    """
    Class which is responsible for methods for brick multiplexing
    operations.
    """

    def get_brick_mux_status(self, server: str) -> str:
        """
        Gets brick multiplex status
        Args:
            server (str): Node on which cmd has to be executed.

        Returns:
            str : Brick multiplex status. None otherwise
        """
        cmd = ("gluster v get all all | grep 'cluster.brick-multiplex' |"
               "awk '{print $2}'")
        ret = self.execute_abstract_op_node(cmd, server, False)
        if ret['error_code'] != 0:
            self.logger.error("Failed to get brick multiplex option value")
        out = ret['msg'][0].split()[0].strip()
        return out

    def is_brick_mux_enabled(self, server: str) -> bool:
        """
        Gets brick multiplex status and checks for positive and
        negative status
        Args:
            server (str): Node on which cmd has to be executed.

        Returns:
            True : Brick multiplex status is one of 'true, on, 1, enable'.
            False : Brick multiplex status is one of 'false, off, 0, disable'.
            Exception : otherwise
        """
        positive_states = ['true', 'on', '1', 'enable']
        negative_states = ['off', 'disable', '0', 'false']
        status = self.get_brick_mux_status(server)
        if status in positive_states:
            return True
        elif status in negative_states:
            return False
        else:
            raise Exception(f"Brick mux status {status} is incorrect")

    def enable_brick_mux(self, server: str) -> bool:
        """
        Enables brick multiplex operation on all servers

        Args:
            server (str): Node on which cmd has to be executed.

        Returns:
            bool : True if successfully enabled brickmux. False otherwise.
        """
        cmd = "gluster v set all cluster.brick-multiplex enable --mode=script"
        ret = self.execute_abstract_op_node(cmd, server, False)
        if ret['error_code'] != 0:
            self.logger.error("Failed to enable brick multiplex")
            return False
        return True

    def disable_brick_mux(self, server: str) -> bool:
        """
        Disables brick multiplex operation on all servers

        Args:
            server (str): Node on which cmd has to be executed.

        Returns:
            bool : True if successfully disabled brickmux. False otherwise.
        """
        cmd = "gluster v set all cluster.brick-multiplex disable --mode=script"
        ret = self.execute_abstract_op_node(cmd, server, False)
        if ret['error_code'] != 0:
            self.logger.error("Failed to disable brick multiplex")
            return False
        return True

    def check_brick_pid_matches_glusterfsd_pid(self, volname: str,
                                               node: str) -> bool:
        """Checks for brick process(es) both volume status
           and 'ps -eaf | grep glusterfsd' matches for
           the given volume

        Args:
            volname (str): Name of the volume.
            node (str): Node on which cmd has to be executed.

        Returns:
            bool : True if pid's matches. False otherwise.
        """
        _rc = True
        bricks_list = self.get_all_bricks(volname, node)
        for brick in bricks_list:
            brick_node, brick_path = brick.split(":")
            ret = self.get_volume_status(volname, node)
            for i in ret[volname]['node']:
                if i['path'] == brick_path:
                    brick_pid = i['pid']
                    break

            cmd = "pgrep -x glusterfsd"
            ret = self.execute_abstract_op_node(cmd, brick_node, False)
            if ret['error_code'] != 0:
                self.logger.error("Failed to get glusterfsdpid on "
                                  f"{brick_node}")
                _rc = False
            else:
                glusterfsd_pid = ret['msg'][0].split()[0].strip()

            if brick_pid not in glusterfsd_pid:
                self.logger.error(f"Brick pid {brick_pid} doesn't match "
                                  "glusterfsd pid {glusterfsd_pid} of "
                                  "the node")
                _rc = False
        return _rc
