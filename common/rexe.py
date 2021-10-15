import os
import time
import random
import concurrent.futures
import json
import paramiko
import xmltodict
from multipledispatch import dispatch


class Rexe:
    def __init__(self, server_dict, client_dict):
        self.host_generic = ['alls', 'allp']
        self.host_dict = {**client_dict, **server_dict}
        self.server_dict = server_dict
        self.client_dict = client_dict

    def _random_node(self):
        """
        Module to select a random node from the
        existing node_dict
        """
        return random.choice(list(self.node_dict.keys()))

    def connect_node(self, node, timeout=None):
        """
        Function to establish connection with the given node.
        """
        if timeout is None:
            timeout_opt = {}
        else:
            timeout_opt = {'timeout': timeout}

        node_ssh_client = paramiko.SSHClient()
        node_ssh_client.load_host_keys(
            os.path.expanduser('~/.ssh/known_hosts'))
        try:
            node_ssh_client.connect(
                hostname=node,
                username='root',
                **timeout_opt
            )
        except Exception as e:
            self.logger.error(f"Connection failure. Exception: {e}")
            self.connect_flag = False
            raise e
        self.node_dict[node] = node_ssh_client

    def establish_connection(self, timeout=15):
        """
        Function to establish connection with the given
        set of hosts.
        """
        self.logger.debug("establish connection")
        self.node_dict = {}
        self.connect_flag = True

        for node in self.host_dict:
            self.connect_node(node, timeout)

    def deconstruct_connection(self):
        """
        Function to close the existing connections.
        """
        self.logger.debug("Deconstructing connection.")
        if not self.connect_flag:
            return
        for node in self.host_dict:
            if self.node_dict[node]:
                (self.node_dict[node]).close()
        return

    @dispatch(str)
    def execute_command(self, cmd):
        """
        Module to handle random node execution.
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed
        """
        return self.execute_command(cmd, self._random_node())

    @dispatch(str, str)
    def execute_command(self, cmd, node):
        """
        Function to execute command in the given node.
        Returns:
            ret: A dictionary consisting
                - Flag : Flag to check if connection failed
                - msg : message
                - error_msg: error message
                - error_code: error code returned
                - cmd : command that got executed
                - node : node on which the command got executed

        """
        ret_dict = {}

        if not self.connect_flag:
            ret_dict['Flag'] = False
            return ret_dict
        try:
            _, stdout, stderr = self.node_dict[node].exec_command(cmd)
        except Exception:
            # Reconnection to be done.
            self.connect_node(node)
            # On rebooting the node
            _, stdout, stderr = self.node_dict[node].exec_command(cmd)

        if stdout.channel.recv_exit_status() != 0:
            ret_dict['Flag'] = False
            ret_dict['msg'] = stdout.readlines()
            ret_dict['error_msg'] = stderr.readlines()
            if isinstance(ret_dict['error_msg'], list):
                ret_dict['error_msg'] = "".join(ret_dict['error_msg'])
        else:
            if cmd.find("--xml") != -1:
                stdout_xml_string = "".join(stdout.readlines())
                ret_dict['msg'] = json.loads(json.dumps(xmltodict.parse(
                    stdout_xml_string)))['cliOutput']
            else:
                ret_dict['msg'] = stdout.readlines()
            ret_dict['Flag'] = True
        ret_dict['node'] = node
        ret_dict['cmd'] = cmd
        ret_dict['error_code'] = stdout.channel.recv_exit_status()

        self.logger.debug(ret_dict)
        return ret_dict

    @dispatch(str)
    def execute_command_async(self, cmd: str) -> dict:
        """
        Module to handle random node async execution.
        Returns:
            ret: A dictionary consisting
                - cmd : Command requested
                - node : Node wherein it was run
                - stdout : The stdout handle
                - stderr : The stderr handle
        """
        return self.execute_command_async(cmd, self._random_node())

    @dispatch(str, str)
    def execute_command_async(self, cmd: str, node: str) -> dict:
        """
        Function to execute command asynchronously in the given node.
        Args:
            cmd (string): Command to be executed.
            node (string) : The node ip wherein the command is to be run.
        Returns:
            ret: A dictionary consisting
                - cmd : Command requested
                - node : Node wherein the command was run
                - stdout : The stdout handle
                - stderr : The stderr handle
        """
        async_obj = {}

        if not self.connect_flag:
            return async_obj
        try:
            stdin, stdout, stderr = self.node_dict[node].exec_command(cmd)
        except Exception:
            # Reconnection to be done.
            self.connect_node(node)
            # On rebooting the node
            stdin, stdout, stderr = self.node_dict[node].exec_command(cmd)

        async_obj = {"cmd": cmd, "node": node, "stdout": stdout,
                     "stderr": stderr, "stdin": stdin}
        return async_obj

    def check_async_command_status(self, async_obj: dict) -> bool:
        """
        A check to see if the async execution of a command which
        was dispatched has been finished.
        Args:
            async_obj (dict) : Contains the details about the async command,
            with keys -> 'stdout', 'stderr', 'cmd', 'node'
        Returns:
            Bool : True if the operations is completed or else False.
        """
        return async_obj["stdout"].channel.exit_status_ready()

    def collect_async_result(self, async_obj: dict) -> dict:
        """
        Collect the async command's execution result after it ends.
        Args:
            async_obj (dict) : Contains the details about the async command,
            with keys -> 'stdout', 'stderr', 'cmd', 'node'
        Returns:
            dict: Returns the resultant dictionary
        """
        ret_dict = {}
        if async_obj['stdout'].channel.recv_exit_status() != 0:
            ret_dict['Flag'] = False
            ret_dict['msg'] = async_obj['stdout'].readlines()
            ret_dict['error_msg'] = async_obj['stderr'].readlines()
            if isinstance(ret_dict['error_msg'], list):
                ret_dict['error_msg'] = "".join(ret_dict['error_msg'])
        else:
            if async_obj['cmd'].find("--xml") != -1:
                stdout_xml_string = "".join(async_obj['stdout'].readlines())
                ret_dict['msg'] = json.loads(json.dumps(xmltodict.parse(
                    stdout_xml_string)))['cliOutput']
            else:
                ret_dict['msg'] = async_obj['stdout'].readlines()
            ret_dict['Flag'] = True
        ret_dict['node'] = async_obj['node']
        ret_dict['cmd'] = async_obj['cmd']
        ret_dict['error_code'] = async_obj['stdout'].channel.recv_exit_status()

        self.logger.debug(ret_dict)
        return ret_dict

    def wait_till_async_command_ends(self, async_obj: dict,
                                     timeout: int = None) -> dict:
        """
        Stay put till the async command finished it's execution and
        provide the required return value.
        Args:
            async_obj (dict) : Contains the details about the async command,
                               with keys -> 'stdout', 'stderr', 'cmd', 'node'
            timeout (int) : Time until which the async command status shall
                            be checked
        Returns:
            dict: Returns the resultant dictionary after the command ends.
        """

        ret_dict = {}
        if timeout:
            while timeout:
                if not async_obj['stdout'].channel.exit_status_ready():
                    time.sleep(1)
                    timeout -= 1
                else:
                    break

            if not timeout:
                ret_dict['error_code'] = -1
                ret_dict['Flag'] = False
                ret_dict['msg'] = ""
                ret_dict['error_msg'] = "Command execution incomplete"
                ret_dict['node'] = async_obj['node']
                ret_dict['cmd'] = async_obj['cmd']
                return ret_dict

        else:
            while not async_obj['stdout'].channel.exit_status_ready():
                time.sleep(1)

        ret_dict = self.collect_async_result(async_obj)
        return ret_dict

    @dispatch(str)
    def execute_command_multinode(self, cmd):
        """
        Function to execute command in multiple nodes parallely
        when node list isn't given.
        """
        return self.execute_command_multinode(cmd, list(self.node_dict.keys()))

    @dispatch(str, list)
    def execute_command_multinode(self, cmd, node_list):
        """
        Function to execute command in multiple nodes
        parallely.
        """
        ret_val = []

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(node_list)) as executor:

            future_exec = {executor.submit(
                self.execute_command, cmd, node): node for node in node_list}
            for future_handle in concurrent.futures.as_completed(future_exec):
                try:
                    ret_val.append(future_handle.result())
                except Exception as exc:
                    print(f"Generated exception : {exc}")
        self.logger.info(ret_val)
        return ret_val

    def transfer_file_from_local(self, source_path, dest_path, dest_node,
                                 remove: bool = False):
        """
        Method to transfer a given file from the source node to the dest node.
        Args:
            source_path (str)
            dest_path (str)
            dest_node (str)
        Optional:
            remove (bool) : If True removes the file and then copies.
                            Defaults to False
        """
        sftp = self.node_dict[dest_node].open_sftp()
        if remove:
            sftp.remove(dest_path)
        sftp.put(source_path, dest_path)
        sftp.close()

    def reboot_node(self, node: str) -> bool:
        """
        Reboot of a node is a special case and we need to execute his using
        paramiko `exec_command` directly.
        Arg:
            node (str)
        Returns:
            bool: True in case command execution was success.
                  False otherwise
        """
        stdout = ""
        self.logger.info(f"Rebooting node: {node} ...")
        cmd = "reboot"
        try:
            _, stdout, _ = self.node_dict[node].exec_command(cmd)
        except Exception as err:
            # In case command execution fails, handle exception
            self.logger.error("Failed to execute 'reboot' command"
                              f"Error: {err}")
            return False

        # Close the channel, if the command executed successfully
        if stdout:
            stdout.close()

        return True
