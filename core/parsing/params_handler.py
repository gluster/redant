"""
This module contains one class - ParamsHandler,
which contains APIs for configuration parameter
parsing.
"""
from parsing.test_parser import Parser


class ParamsHandler:
    """
    This class contains all the APIs required for fetching
    the values of all the configuration parameters.
    """

    @classmethod
    def get_config_hashmap(cls, filepath: str):
        """
        Gets the configuration hashmap generated from the
        api in Parser class and sets the reuired class variable.
        The config_hashmap class variable can be accessed
        throughout the class.
        Args:
            filepath (str): Path for config file
        """
        cls.config_hashmap = Parser.generate_config_hashmap(filepath)

    @classmethod
    def get_server_ip(cls, server_name: str) -> str:
        """
        Gives the server ip given the server name
        Args:
            server_name: name of the server as in config file.
                         example: server-vm1
        Returns:
            str: ip address of the given server
        Example:
            get_server_ip("server-vm1")
        """
        server_ip = cls.config_hashmap['servers_info'][server_name]["ip"]
        return server_ip

    @classmethod
    def get_client_ip(cls, client_name: str) -> str:
        """
        Gives the client ip given the client name
        Args:
            client_name: name of the client as in config file.
                         example: client_vm1
        Returns:
            ip address of the given client
        Example:
            str: get_client_ip("client_vm1")
        """
        client_ip = cls.config_hashmap['clients_info'][client_name]["ip"]
        return client_ip

    @classmethod
    def get_server_ip_list(cls) -> list:
        """
        Gives the list of all server ip
        Returns:
            list: list of all server ip address
        """ 
        servers = list(cls.config_hashmap['servers_info'].keys())
        server_ip_list = []
        for server in servers:
            server_ip_list.append(cls.get_server_ip(server))
        return server_ip_list
        

    @classmethod
    def get_client_ip_list(cls) -> list:
        """
        Gives the list of all client ip
        Returns:
            list: list of all client ip address
        """
        clients = list(cls.config_hashmap['clients_info'].keys())
        client_ip_list = []
        for client in clients:
            client_ip_list.append(cls.get_client_ip(client))
        return client_ip_list

    @classmethod
    def get_nodes_info(cls) -> dict:
        """
        Returns a dictionary consisting of server info
        Returns:
            dict: dictionary consisting of server info
        format of dictionary:
        {
            servers: {
                        "server1": {
                            "ip" : 10.4.28.93
                            "user" : root
                            "passwd" : redhat
                        },
                        "server2": {
                            "ip" : 23.43.12.87
                            "user" : root
                            "passwd" : redhat
                        }
            }
            clients: {
                        "client1": {
                            "ip" : 10.3.28.92
                            "user" : root
                            "passwd" : redhat
                        },
                        "client2": {
                            "ip" : 15.12.43.98
                            "user" : root
                            "passwd" : redhat
                        }
           }
        }
        """

        nodes_info = {}
        s_info = cls.config_hashmap["servers_info"]
        c_info = cls.config_hashmap["clients_info"]
        
        servers = list(s_info.keys())
        
        for server in servers:
            s_info[server].pop("brick_root")
            
        nodes_info['servers'] = s_info
        nodes_info['clients'] = c_info

        return nodes_info

    @classmethod
    def get_brick_root_list(cls, server_name: str) -> list:
        """
        Returns the list of brick root given the server name
        Args:
            server_name (str): name of the server as in config file.
                         example: server-vm1
        Returns:
            list: list of brick root of the given server
        Example:
            get_brick_root_list("server-vm1")
        """
        servers_info = cls.config_hashmap['servers_info']
        brick_root_list = servers_info[server_name]['brick_root']
        return brick_root_list
