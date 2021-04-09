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

    def start_glusterd(self, node, enable_retry: bool=True):
        """
        Starts the glusterd service on the specified node or nodes.
        Args:
            node (str|list): The node(s) on which the glusterd service
                             is to be started.
        """
        cmd_fail = False
        error_msg = ""
        if not isinstance(node, list):
            node = [node]

        cmd = "pgrep glusterd || systemctl start glusterd"

        self.logger.info(f"Running {cmd} on {node}")

        ret = self.execute_command_multinode(node, cmd)

        for result_val in ret:
            if int(result_val['error_code']) != 0:
                error_msg = result_val['error_msg']
                self.logger.error(error_msg)
                cmd_fail = True
                break

        if cmd_fail and enable_retry:
            self.reset_failed_glusterd(node)
            self.start_glusterd(node)
        elif cmd_fail:
            raise Exception(error_msg)

        self.logger.info(f"Successfully ran {cmd} on {node}")

    def restart_glusterd(self, node: str, enable_retry: bool=True):
        """
        Restarts the glusterd service on the specified node or nodes.
        Args:
            node (str|list): The node(s) on which the glusterd service
                             is to be restarted.
        """
        cmd_fail = False
        error_msg = ""
        if not isinstance(node, list):
            node = [node]

        cmd = "systemctl restart glusterd"

        self.logger.info(f"Running {cmd} on {node}")

        ret = self.execute_command_multinode(node, cmd)

        for result_val in ret:
            if int(result_val['error_code']) != 0:
                error_msg = result_val['error_msg']
                self.logger.error(error_msg)
                cmd_fail = True
                break

        if cmd_fail and enable_retry:
            self.reset_failed_glusterd(node)
            self.restart_glusterd(node)
        elif cmd_fail:
            raise Exception(error_msg)

        self.logger.info(f"Successfully ran {cmd} on {node}")

    def stop_glusterd(self, node):
        """
        Stops the glusterd service on the specified node(s).
        Args:
            node (str|list): The node on which the glusterd service
                        is to be stopped.
        """
        cmd = "systemctl stop glusterd"

        if not isinstance(node, list):
            node = [node]

        self.logger.info(f"Running {cmd} on {node}")

        ret = self.execute_command_multinode(node, cmd)

        for result_val in ret:
            if int(result_val['error_code']) != 0:
                self.logger.error(result_val['error_msg'])
                raise Exception(result_val['error_msg'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

    def reset_failed_glusterd(self, node) -> bool:
        """
        Glusterd has a burst limit of 5 times, hence TCs will
        start failing after the TC breach this limit. Systemd has
        the feature to reset the limit which is of the form,
        `systemctl reset-failed <daemon-process-name>`

        Args:
            node (str|list): A node or list of nodes on which glusterd
            reset-failed has to be run.

        Returns:
            bool: True if successful on all servers or false.
        """
        if not isinstance(node, list):
            node = [node]

        cmd = "systemctl reset-failed glusterd"

        self.logger.info(f"Running {cmd} on {node}")

        ret = self.execute_command_multinode(node, cmd)
        for result_val in ret:
            if int(result_val['error_code']) != 0:
                self.logger.error(result_val['error_msg'])
                raise Exception(result_val['error_msg'])

        self.logger.info(f"Successfully ran {cmd} on {node}")

    def is_glusterd_running(self, node: str) -> bool:
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

        self.logger.info(f"Running {cmd1} on {node}")

        ret = self.execute_command(node=node, cmd=cmd1)

        if int(ret['error_code']) != 0:
            is_active = 0
            self.logger.info(f"Running {cmd2} on {node}")
            ret1 = self.execute_command(node=node, cmd=cmd2)
            if ret1['error_code'] == 0:
                is_active = -1
                self.logger.info(f"Successfully ran {cmd2} on {node}")

        self.logger.info(f"Successfully ran {cmd1} on {node}")
        return is_active

    def wait_for_glusterd_to_start(self, node, timeout: int=80):
        """
        Checks if the glusterd has started already or waits for
        it till the timeout is reached.

        Args:
            node (str|list): A node or list of nodes wherein this is
            to be executed.
            timeout (int) : We cannot wait till eternity right :p

        Returns:
            bool: True if glusterd is running on the node(s) or else False.
        """
        if not isinstance(node, list):
            node = [node]

        count = 0
        from time import sleep
        while count <= timeout:
            ret = self.is_glusterd_running(node)
            if not ret:
                return True
            sleep(1)
            count += 1
        return False

    # TODO: Handle command execution in such a manner that this doesn't
    # go under xml version.
    def get_gluster_version(self, node: str) -> str:
        """
        Checks the glusterfs version on the node.

        Args:
            node (str): Node wherein the gluster version is
            checked.

        Returns:
            str: The gluster version value.
        """
        cmd = "gluster --version"
        self.logger.info(f"Running {cmd} on {node}")

        ret = self.execute_command(node=node, cmd=cmd)

        if int(ret['error_code']) != 0:
            self.logger.error(ret['error_msg'])
            raise Exception(ret['error_msg'])

        self.logger.info("Successfully ran {cmd} on {node}")
        return ret['msg'].split(' ')[1]
