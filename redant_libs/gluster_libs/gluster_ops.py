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

    def gluster_start(self, node: str):
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

    def gluster_stop(self, node: str):
        """
        Stops the glusterd service on the specified node.
        Args:
            node (str): The node on which the glusterd service
                        is to be stopped.
        """
        cmd = "systemctl sto glusterd"

        self.rlog(f"Running {cmd} on {node}")

        ret = self.execute_command(node=node, cmd=cmd)
        print(ret)
        if int(ret['error_code']) != 0:
            self.rlog(ret['error_msg'], 'E')
            raise Exception(ret['error_msg'])

        self.rlog("Successfully ran {cmd} on {node}")
