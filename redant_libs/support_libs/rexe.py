from os import path
import concurrent.futures
import paramiko
import yaml
import xmltodict

def is_file_accessible(path, mode='rw+'):
    """
    Check if the file or directory at `path` can
    be accessed by the program using `mode` open flags.
    """
    try:
        f = open(path, mode)
        f.close()
    except IOError:
        return False
    return True

class Rexe:
    def __init__(self, conf_path, command_file_path=""):
        self.host_generic = ['alls', 'allp']
        self.conf_path = conf_path
        self.command_file_path = command_file_path
        self.parse_conf_file()
        if command_file_path != "":
            self.parse_exec_file()
        self.rlog(f"Conf file data : {self.conf_data}", 'D')

    def parse_conf_file(self):
        """
        Function to parse the config file to get
        the host details, host username and host password.
        """
        self.conf_file_handle = open(self.conf_path)
        self.conf_data = yaml.load(self.conf_file_handle, Loader=yaml.FullLoader)
        self.conf_file_handle.close()
        self.host_list = self.conf_data['host_list']
        self.host_user = self.conf_data['user']
        self.host_passwd = self.conf_data['passwd']

    def parse_exec_file(self):
        """
        Function to parse the exec file
        """
        self.rlog("Parsing exec file", 'D')
        self.exec_file_handle = open(self.command_file_path)
        self.exec_data = yaml.load(self.exec_file_handle, Loader=yaml.FullLoader)
        self.conf_file_handle.close()
        self.rlog(f"Exec file data : {self.exec_data}", 'D')

    def establish_connection(self):
        """
        Function to establish connection with the given
        set of hosts.
        """
        self.rlog("establish connection", 'D')
        self.node_dict = {}
        self.connect_flag = True
        
        for node in self.host_list:
            node_ssh_client = paramiko.SSHClient()
            node_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                node_ssh_client.connect(hostname=node, username=self.host_user, password=self.host_passwd)
                self.rlog(f"SSH connection to {node} is successful.", 'D')
            except paramiko.ssh_exception.AuthenticationException:
                self.rlog("Authentication failure. Please check conf.", 'E')
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
        stdin, stdout, stderr = self.node_dict[node].exec_command(cmd)
        if stdout.channel.recv_exit_status() != 0:
            ret_dict['Flag'] = False
            ret_dict['msg'] = stdout.readlines()
            ret_dict['error_msg'] = stderr.readlines()
        else:
            if cmd.split(' ', 1)[0] == 'gluster':
                stdout_xml_string = ""
                for line in stdout.readlines():
                    stdout_xml_string += line
                ret_dict['msg'] = xmltodict.parse(stdout_xml_string)['cliOutput']
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
        with concurrent.futures.ThreadPoolExecutor(max_workers = len(node_list)) as executor:
            future_exec = {executor.submit(self.execute_command, node, cmd): node for node in node_list}
            for future_handle in concurrent.futures.as_completed(future_exec):
                try:
                    ret_val.append(future_handle.result())
                except Exception as exc:
                    print(f"Generated exception : {exc}")
        self.rlog(ret_val)
        return ret_val

    def execute_command_file(self):
        """
        Function to execute the commands provided in the
        command file.
        """
        if self.command_file_path == "":
            return -1
        for command_node in self.exec_data:
            if command_node not in self.host_list and command_node not in self.host_generic:
                self.rlog(f"The command node {command_node} is not in host list.")
                continue
            commands_list = self.exec_data[command_node]
            if command_node == 'allp':
                # This is for parallel execution of commands in all nodes.
                for command in commands_list:
                    self.execute_command_multinode(self.host_list, command)
            elif command_node == 'alls':
                # Sequential execution of commands in all nodes.
                for command in commands_list:
                    for node in self.host_list:
                        self.execute_command(node, command)
            else:
                for command in commands_list:
                    self.execute_command(command_node, command)
