import os
import time
import random
import concurrent.futures
import json
import paramiko
import xmltodict
from multipledispatch import dispatch


class Rexe:
    def __init__(self, host_dict):
        self.host_generic = ['alls', 'allp']
        self.host_dict = host_dict

    def _random_node(self):
        """
        Module to select a random node from the
        existing node_dict
        """
        return random.choice(list(self.node_dict.keys()))

    def establish_connection(self, timeout=15):
        """
        Function to establish connection with the given
        set of hosts.
        """
        self.logger.debug("establish connection")
        self.node_dict = {}
        self.connect_flag = True

        for node in self.host_dict:

            node_ssh_client = paramiko.SSHClient()
            node_ssh_client.load_host_keys(
                os.path.expanduser('/root/.ssh/known_hosts'))
            mykey = paramiko.RSAKey.from_private_key_file('/root/.ssh/id_rsa')
            try:
                node_ssh_client.connect(
                    hostname=node,
                    pkey=mykey,
                    timeout=timeout,
                )
            except Exception as e:
                self.logger.error(f"Connection failure. Exception : {e}")
                self.connect_flag = False
                raise e
            self.node_dict[node] = node_ssh_client

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
        except Exception as e:
            # Reconnection to be done.
            node_ssh_client = paramiko.SSHClient()
            node_ssh_client.load_host_keys(
                os.path.expanduser('/root/.ssh/known_hosts'))
            mykey = paramiko.RSAKey.from_private_key_file('/root/.ssh/id_rsa')
            try:
                node_ssh_client.connect(
                    hostname=node,
                    pkey=mykey,
                )
                self.node_dict[node] = node_ssh_client
            except Exception as e:
                self.logger.error(f"Connection failure. Exceptions {e}.")
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
            _, stdout, stderr = self.node_dict[node].exec_command(cmd)
            async_obj = {"cmd": cmd, "node": node, "stdout": stdout,
                         "stderr": stderr}
        except Exception as e:
            # Reconnection to be done.
            node_ssh_client = paramiko.SSHClient()
            node_ssh_client.load_host_keys(
                os.path.expanduser('/root/.ssh/known_hosts'))
            mykey = paramiko.RSAKey.from_private_key_file('/root/.ssh/id_rsa')
            try:
                node_ssh_client.connect(
                    hostname=node,
                    pkey=mykey,
                )
                self.node_dict[node] = node_ssh_client
            except Exception as e:
                self.logger.error(f"Connection failure. Exceptions {e}.")
            # On rebooting the node
            _, stdout, stderr = self.node_dict[node].exec_command(cmd)

            async_obj = {"cmd": cmd, "node": node, "stdout": stdout,
                         "stderr": stderr}
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

    def wait_till_async_command_ends(self, async_obj: dict) -> dict:
        """
        Stay put till the async command finished it's execution and
        provide the required return value.
        Args:
            async_obj (dict) : Contains the details about the async command,
            with keys -> 'stdout', 'stderr', 'cmd', 'node'
        Returns:
            dict: Returns the resultant dictionary after the command ends.
        """
        while not async_obj['stdout'].channel.exit_status_ready():
            time.sleep(1)
            if async_obj['stdout'].channel.recv_ready():
                ret_dict = self.collect_async_result(async_obj)
                break

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
