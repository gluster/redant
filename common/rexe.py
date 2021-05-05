import os
import random
import concurrent.futures
import paramiko
import xmltodict
import json
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

    def establish_connection(self):
        """
        Function to establish connection with the given
        set of hosts.
        """
        self.logger.debug("establish connection")
        self.node_dict = {}
        self.connect_flag = True

        for node in self.host_dict:

            node_ssh_client = paramiko.SSHClient()
            node_ssh_client.load_host_keys(os.path.expanduser('/root/.ssh/known_hosts'))
            mykey = paramiko.RSAKey.from_private_key_file('/root/.ssh/id_rsa')
            try:
                node_ssh_client.connect(
                    hostname=node,
                    pkey=mykey,
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
            node_ssh_client.load_host_keys(os.path.expanduser('/root/.ssh/known_hosts'))
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

        # Wait till command completes.
        while not stdout.channel.exit_status_ready():
            time.sleep(1)
            if stdout.channel.recv_ready():
                break

        if stdout.channel.recv_exit_status() != 0:
            ret_dict['Flag'] = False
            ret_dict['msg'] = stdout.readlines()
            ret_dict['error_msg'] = stderr.readlines()
            if isinstance(ret_dict['error_msg'], list):
                ret_dict['error_msg'] = "".join(ret_dict['error_msg'])
        else:
            # Gluster related commands use --xml flag for more info on response
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
