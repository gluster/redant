"""
This file contains one class - GlusterOps wich holds
operations on the glusterd service on the server
or the client.
"""


class GlusterOps:
    """
    GlusterOps class provides APIs to start and stop
    the glusterd service on either the client or the sever.
    """

    def glusterd_start(self, node: str):
        """
        Starts the glusterd service on the specified node.
        Args:
            node (str): The node on which the glusterd service
                        is to be started.
        """
        cmd = "systemctl start glusterd"

        self.rlog(f"Running {cmd} on {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['error_code']) != 0:
            self.rlog(ret['error_msg'], 'E')
            raise Exception(ret['error_msg'])

        self.rlog("Successfully ran {cmd} on {node}")

    def glusterd_stop(self, node: str):
        """
        Stops the glusterd service on the specified node.
        Args:
            node (str): The node on which the glusterd service
                        is to be stopped.
        """
        cmd = "systemctl stop glusterd"

        self.rlog(f"Running {cmd} on {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['error_code']) != 0:
            self.rlog(ret['error_msg'], 'E')
            raise Exception(ret['error_msg'])

        self.rlog("Successfully ran {cmd} on {node}")

    def is_glusterd_active(self, node: str) -> bool:
        """
        Checks the status of the glusterd service on the
        specified node.
        Args:
            node (str): The node on which the glusterd service
                        is to be stopped.
        Returns:
            1  : if glusterd active
            0  : if glusterd not active
           -1  : if glusterd not active and PID is alive
        """
        is_active = 1
        cmd1 = "systemctl status glusterd"
        cmd2 = "pidof glusterd"

        self.rlog(f"Running {cmd1} on {node}")

        ret = self.execute_command(node=node, cmd=cmd1)

        if int(ret['error_code']) != 0:
            is_active = 0
            self.rlog(f"Running {cmd2} on {node}")
            ret1 = self.execute_command(node=node, cmd=cmd2)
            if ret1['error_code'] == 0:
                is_active = -1
                self.rlog("Successfully ran {cmd2} on {node}")

        self.rlog("Successfully ran {cmd1} on {node}")
        return is_active
