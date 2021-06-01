"""
This file contains one class - GlusterOps wich holds
operations on the glusterd service on the server
or the client.
"""
from time import sleep
import configparser
from common.ops.abstract_ops import AbstractOps


class GlusterOps(AbstractOps):
    """
    GlusterOps class provides APIs to start and stop
    the glusterd service on either the client or the sever.
    """

    def start_glusterd(self, node=None, enable_retry: bool = True) -> dict:
        """
        Starts the glusterd service on the specified node or nodes.
        Args:
            node (str|list): The node(s) on which the glusterd service
                             is to be started.
            enable_retry (bool): If true a retry takes place else not.
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """
        cmd_fail = False
        error_msg = ""
        if not isinstance(node, list) and node is not None:
            node = [node]

        cmd = "pgrep glusterd || systemctl start glusterd"

        if node is None:
            ret = self.execute_command_multinode(cmd)
            self.logger.info(f"Running {cmd} on all nodes.")
        else:
            ret = self.execute_command_multinode(cmd, node)
            self.logger.info(f"Running {cmd} on {node}")

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

        return ret

    def restart_glusterd(self, node: str, enable_retry: bool = True) -> dict:
        """
        Restarts the glusterd service on the specified node or nodes.
        Args:
            node (str|list): The node(s) on which the glusterd service
                             is to be restarted.
            enable_retry (bool): If true a retry takes places
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """
        cmd_fail = False
        error_msg = ""
        if not isinstance(node, list) and node is not None:
            node = [node]

        cmd = "systemctl restart glusterd"

        self.logger.info(f"Running {cmd} on {node}")

        ret = self.execute_command_multinode(cmd, node)

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

        return ret

    def stop_glusterd(self, node=None) -> dict:
        """
        Stops the glusterd service on the specified node(s).
        Args:
            node (str|list): The node on which the glusterd service
                        is to be stopped.
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """
        cmd = "systemctl stop glusterd"

        if not isinstance(node, list) and node is not None:
            node = [node]

        if node is None:
            self.logger.info(f"Running {cmd} on all nodes")
            ret = self.execute_command_multinode(cmd)
        else:
            self.logger.info(f"Running {cmd} on {node}")
            ret = self.execute_command_multinode(cmd, node)

        for result_val in ret:
            if int(result_val['error_code']) != 0:
                self.logger.error(result_val['error_msg'])
                raise Exception(result_val['error_msg'])

        return ret

    def reset_failed_glusterd(self, node=None) -> bool:
        """
        Glusterd has a burst limit of 5 times, hence TCs will
        start failing after the TC breach this limit. Systemd has
        the feature to reset the limit which is of the form,
        `systemctl reset-failed <daemon-process-name>`

        Args:
            node (str|list): A node or list of nodes on which glusterd
            reset-failed has to be run.

        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """
        if not isinstance(node, list) and node is not None:
            node = [node]

        cmd = "systemctl reset-failed glusterd"

        if node is None:
            ret = self.execute_command_multinode(cmd)
            self.logger.info(f"Running {cmd} on all nodes.")
        else:
            ret = self.execute_command_multinode(cmd, node)
            self.logger.info(f"Running {cmd} on {node}")
        for result_val in ret:
            if int(result_val['error_code']) != 0:
                self.logger.error(result_val['error_msg'])
                raise Exception(result_val['error_msg'])

        return ret

    def is_glusterd_running(self, servers: list) -> bool:
        """
        Checks the status of the glusterd service on the
        specified servers.
        Args:
            servers (str|list): A server|list of server on which the glusterd
                                service status has to be checked.
        Returns:
            1  : if glusterd active
            0  : if glusterd not active
           -1  : if glusterd not active and PID is alive
        """
        if not isinstance(servers, list):
            servers = [servers]

        cmd1 = "systemctl status glusterd"
        cmd2 = "pidof glusterd"

        ret1 = self.execute_command_multinode(cmd1, servers)

        is_active = 1
        for ret_value in ret1:
            if int(ret_value['error_code']) != 0:
                is_active = 0
                self.logger.error(f"Glusterd is not running on "
                                  f"{ret_value['node']}")
                ret2 = self.execute_command(cmd2, ret_value['node'])
                if ret2['error_code'] == 0:
                    is_active = -1

        return is_active

    def wait_for_glusterd_to_start(self, node: str, timeout: int = 80) -> bool:
        """
        Checks if the glusterd has started already or waits for
        it till the timeout is reached.

        Args:
            node (str|list): Node on which this is to be executed.
            timeout (int) : We cannot wait till eternity right :p

        Returns:
            bool: True if glusterd is running on the node or else False.
        """
        count = 0
        while count <= timeout:
            ret = self.is_glusterd_running(node)
            if ret == 1:
                return True
            sleep(1)
            count += 1
        return False

    def wait_for_glusterd_to_stop(self, node: str, timeout: int = 80) -> bool:
        """
        Checks if the glusterd has stopeed already or waits for
        it till the timeout is reached.

        Args:
            node (str|list): Node on which this is to be executed.
            timeout (int) : We cannot wait till eternity right :p

        Returns:
            bool: True if glusterd is not running on the node or else False.
        """
        count = 0
        while count <= timeout:
            ret = self.is_glusterd_running(node)
            if ret == 0:
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

        ret = self.execute_abstract_op_node(cmd, node)

        return ret['msg'][0].rstrip('\n').split(' ')[1]

    def get_state(self, node: str) -> dict:
        """
        Function to get the gluster state data.

        Args:
            node (str): Node wherein the command is to be run.
        Returns:
            State dictionary.
        """
        cmd = ("gluster get-state")

        ret = self.execute_abstract_op_node(cmd, node)
        file_path = ret['msg'][0][ret['msg'][0].find('/'):-1]

        cmd = (f"cat {file_path}")
        ret = self.execute_abstract_op_node(cmd, node)
        state_string_val = "".join(ret['msg'])
        config = configparser.ConfigParser()
        config.read_string(state_string_val)
        return {section: dict(config.items(section)) for section in
                config.sections()}

    def get_glusterd_process_count(self, node: str) -> int:
        """
        Get the gluster process count for a given node.

        Args:
            node (str): Node on which glusterd process has to be counted.

        Returns:
            int: Number of glusterd processes running on the node.
            None: If the command fails to execute.
        """
        ret = self.execute_abstract_op_node("pgrep -c glusterd", node,
                                            False)
        if ret['error_code'] == 0:
            count_of_proc = int(ret['msg'][0].rstrip('\n'))
            return count_of_proc
        else:
            return None

    def get_all_gluster_process_count(self, node: str) -> int:
        """
        Get all gluster related process count for a given node.

        Args:
            node (str): Node on which gluster process has to be counted.

        Returns:
            int: Number of gluster processes running on the node.
            None: If the command fails to execute.
        """
        cmd = "pgrep -c '(glusterd|glusterfsd|glusterfs)'"
        ret = self.execute_abstract_op_node(cmd, node, False)
        if ret['error_code'] == 0:
            count_of_proc = int(ret['msg'][0].rstrip('\n'))
            return count_of_proc
        else:
            return None
