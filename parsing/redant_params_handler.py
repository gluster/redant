"""
This module contains one class - ParamsHandler,
which contains APIs for configuration parameter
parsing.
"""
from parsing.redant_test_parser import Parser


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
                         example: server_vm1
        Returns:
            str: ip address of the given server
        Example:
            get_server_ip("server_vm1")
        """
        index = server_name[9:]
        server_ip = cls.config_hashmap['servers'][int(index)-1]
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
        index = client_name[9:]
        client_ip = cls.config_hashmap['clients'][int(index)-1]
        return client_ip

    @classmethod
    def get_server_ip_list(cls) -> list:
        """
        Gives the list of all server ip
        Returns:
            list: list of all server ip address
        """
        server_ip_list = cls.config_hashmap['servers']
        return server_ip_list

    @classmethod
    def get_client_ip_list(cls) -> list:
        """
        Gives the list of all client ip
        Returns:
            list: list of all client ip address
        """
        client_ip_list = cls.config_hashmap['clients']
        return client_ip_list

    @classmethod
    def get_brick_root_list(cls, server_name: str) -> list:
        """
        Returns the list of brick root given the server name
        Args:
            server_name (str): name of the server as in config file.
                         example: server_vm1
        Returns:
            list: list of brick root of the given server
        Example:
            get_brick_root_list("server_vm1")
        """
        server_ip = cls.get_server_ip(server_name)
        servers_info = cls.config_hashmap['servers_info']
        brick_root_list = servers_info[server_ip]['brick_root']
        return brick_root_list

    @classmethod
    def volume_create_force_option(cls) -> bool:
        """
        Returns the flag for volume_create_force option
        Returns:
            bool: flag value(True/False) for volume_create_force option
        """
        gluster_info = cls.config_hashmap['gluster']
        volume_create_force = gluster_info['volume_create_force']
        return volume_create_force
