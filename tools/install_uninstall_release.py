"""
This script can be used for
installing, uninstalling a specific release
of glusterfs. If you want to upgrade or degrade from
a release to another it will come out as a
handy tool as well :)
"""

import os
from os import listdir
from os.path import isfile, join
from simple_term_menu import TerminalMenu
import paramiko
from scp import SCPClient
import json


class Script:

    @classmethod
    def _make_choices(cls):
        """
        This method shows the menu
        and gets the choice as input from the user
        """
        cls.choice = {}

        print(f"Select the OS to install its rpms or press q to cancel.")
        os_types = ["Fedora-32", "Fedora-33", "Centos-8"]
        operations = ['Install', "Uninstall", "Upgrade/Degrade"]
        release_types = ['release-10', 'release-9']

        os_menu = TerminalMenu(
            os_types, title="Operating System:", menu_cursor_style=("fg_green", "bold"))
        os_index = os_menu.show()
        if os_index != None:
            cls.choice['os'] = os_types[os_index]

            options_menu = TerminalMenu(operations, title="Operations")
            operation_index = options_menu.show()
            if operation_index != None:
                cls.choice['operation'] = operation_index
            else:
                cls.choice['operation'] = 0

            if operation_index != 2:
                release_menu = TerminalMenu(
                    release_types, title="Release Types:")
                release_index = release_menu.show()
                if release_index != None:
                    cls.choice['release'] = [release_types[release_index]]
                else:
                    cls.choice['release'] = [release_types[0]]
            else:
                release_menu = TerminalMenu(
                    release_types, title="New Release:")
                release_index = release_menu.show()
                if release_index != None:
                    cls.choice['release'] = [release_types[release_index]]
                else:
                    cls.choice['release'] = [release_types[0]]

                release_menu = TerminalMenu(
                    release_types, title="Old release:")
                release_index = release_menu.show()
                if release_index != None:
                    cls.choice['release'].append(release_types[release_index])
                else:
                    cls.choice['release'].append(release_types[0])

            if cls.choice['os'] != None and cls.choice['release'] != None:
                print(
                    f'''
                    Selections\n
                    ===========\n
                    Os:{cls.choice['os']}\n
                    Operation:{operations[cls.choice['operation']]}\n
                    Release:{cls.choice['release']}\n
                    '''
                )
        else:
            print("No os chosen")
            exit()

    @classmethod
    def _generate_list_of_rpms(cls):
        """
        This method generates the list
        of rpms that are to be installed
        on the chosen operating system
        and for the specific release
        """

        cls.rpms_list = []

        cls.rpm_path = f"{os.path.abspath('gluster-rpms')}/{cls.choice['os']}/{cls.choice['release'][0]}/"
        for each_rpm in os.listdir(cls.rpm_path):
            cls.rpms_list.append(cls.rpm_path + each_rpm)

    @classmethod
    def _establish_connection(cls, host: str):
        """
        This method establises
        connection with the host

        Args: 
        host: The server on which we will
            establish the connection
        """
        node_ssh_client = paramiko.SSHClient()
        node_ssh_client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        try:
            node_ssh_client.connect(
                hostname=host,
                username='root',
                password='redhat')
            print(f"SSH connection to 10.70.43.184 is successful.")
        except Exception as e:
            print(f"Connection failure. Exception : {e}")

        return node_ssh_client

    @classmethod
    def _execute_command(cls, comm: str, input_flag: bool = False, input_str: str = None):
        """
        This method executes
        the command comm on the
        host
        """
        ret_dict = {}

        try:
            stdin, stdout, stderr = cls.node_ssh_client.exec_command(comm)

            if input_flag:
                stdin.write(input_str)
                stdin.flush()

        except Exception as e:
            print(e)

        if stdout.channel.recv_exit_status() != 0:
            ret_dict['error'] = stderr.readlines()
        else:
            ret_dict['msg'] = stdout.readlines()
            # ret['input'] = stdin.readlines()
        ret_dict['error_code'] = stdout.channel.recv_exit_status()

        print(json.dumps(ret_dict, indent=4))
        return ret_dict

    @classmethod
    def _create_dir_structure(cls):
        """
        This method creates a directory structure
        in the remote server
        """
        cls.remote_os_path = f"/home/rpm_install/rpms/{cls.choice['os']}/"
        msg = cls._execute_command(f'mkdir -p {cls.remote_os_path}')

    @classmethod
    def _copy_files_to_server(cls):
        """
        This method copies rpms
        to the server
        """
        scp = SCPClient(cls.node_ssh_client.get_transport())
        scp.put(cls.rpm_path[:-1], recursive=True,
                remote_path=cls.remote_os_path)
        print(f"Copied the files in {cls.remote_os_path}")
        scp.put(os.path.abspath("remote_handler.py"),
                remote_path=cls.remote_os_path+cls.choice['release'][0])

    @classmethod
    def _perform_operation(cls):
        """
        This function will perform
        the operation chosen by the user
        """
        if cls.choice['operation'] == 0:
            print("Installing the following release")
            # createrepo and install

        elif cls.choice['operation'] == 1:
            print("Uninstalling the release")
        else:
            print("Upgrading/Degrasing")

    @classmethod
    def main(cls):
        """
        This is the method that takes
        care of the complete operation
        """
        cls._make_choices()
        cls._generate_list_of_rpms()
        cls.node_ssh_client = cls._establish_connection('10.70.43.184')

        cls._create_dir_structure()

        cls._perform_operation()

if __name__ == "__main__":
    Script.main()
