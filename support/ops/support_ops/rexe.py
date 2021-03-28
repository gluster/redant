import concurrent.futures
import paramiko
import yaml
import xmltodict


class Rexe:
    def __init__(self, host_dict):
        self.host_generic = ['alls', 'allp']
        self.host_dict = {}
        for element in host_dict:
            self.host_dict[element['hostname']] = {}
            self.host_dict[element['hostname']]['user'] = element['user']
            self.host_dict[element['hostname']]['passwd'] = element['passwd']
            self.host_dict[element['hostname']]['ip'] = element['ip']

    def establish_connection(self):
        """
        Function to establish connection with the given
        set of hosts.
        """
        self.rlog("establish connection", 'D')
        self.node_dict = {}
        self.connect_flag = True

        for node in self.host_dict:
            node_ssh_client = paramiko.SSHClient()
            node_ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            try:
                node_ssh_client.connect(
                    hostname=self.host_dict[node]['ip'],
                    username=self.host_dict[node]['user'],
                    password=self.host_dict[node]['passwd'])
                self.rlog(f"SSH connection to {node} is successful.", 'D')
            except Exception as e:
                self.rlog(f"Connection failure. Exception : {e}", 'E')
                self.connect_flag = False
            self.node_dict[node] = node_ssh_client

    def execute_command(self, node, cmd):
        """
        Function to execute command in the given node.
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
            node_ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            try:
                node_ssh_client.connect(
                    hostname=self.host_dict[node]['ip'],
                    username=self.host_dict[node]['user'],
                    password=self.host_dict[node]['passwd'])
                self.rlog(f"SSH connection to {node} is successful.", 'D')
                self.node_dict[node] = node_ssh_client
            except Exception as e:
                self.rlog(f"Connection failure. Exception : {e}", 'E')
        if stdout.channel.recv_exit_status() != 0:
            ret_dict['Flag'] = False
            ret_dict['msg'] = stdout.readlines()
            ret_dict['error_msg'] = stderr.readlines()
        else:
            if cmd.split(' ', 1)[0] == 'gluster':
                stdout_xml_string = "".join(stdout.readlines())
                ret_dict['msg'] = xmltodict.parse(
                    stdout_xml_string)['cliOutput']
            else:
                ret_dict['msg'] = stdout.readlines()
            ret_dict['Flag'] = True
        ret_dict['node'] = node
        ret_dict['cmd'] = cmd
        ret_dict['error_code'] = stdout.channel.recv_exit_status()

        self.rlog(ret_dict, 'D')
        return ret_dict

    def execute_command_multinode(self, node_list, cmd):
        """
        Function to execute command in multiple nodes
        parallely.
        """
        ret_val = []
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(node_list)) as executor:

            future_exec = {executor.submit(
                self.execute_command, node, cmd): node for node in node_list}
            for future_handle in concurrent.futures.as_completed(future_exec):
                try:
                    ret_val.append(future_handle.result())
                except Exception as exc:
                    print(f"Generated exception : {exc}")
        self.rlog(ret_val)
        return ret_val
