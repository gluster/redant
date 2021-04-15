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
    def set_config_hashmap(cls, filepath: str):
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
    def get_server_ip_list(cls) -> list:
        """
        Gives the list of all server ip
        Returns:
            list: list of all server ip address
        """ 
        server_ip_list = list(cls.config_hashmap['servers_info'].keys())
        return server_ip_list
        

    @classmethod
    def get_client_ip_list(cls) -> list:
        """
        Gives the list of all client ip
        Returns:
            list: list of all client ip address
        """
        client_ip_list = list(cls.config_hashmap['clients_info'].keys())
        return client_ip_list

    @classmethod
    def get_config_hashmap(cls) -> dict:
        """
        Returns the config hashmap which is parsed from
        the config file 
        Returns:
            dict: dictionary consisting of servers info,
                  clients info and volume types info. 
            format of dictionary:
            {
                servers_info: {
                                "10.4.28.93": {
                                    "user" : root
                                    "passwd" : redhat
                                },
                                "23.43.12.87": { 
                                    "user" : root
                                    "passwd" : redhat
                                }
                }
                clients_info: {
                                "10.3.28.92": {
                                    "user" : root
                                    "passwd" : redhat
                                },
                                "15.12.43.98": {
                                    "user" : root
                                    "passwd" : redhat
                                }
               }
               volume_types: {
                                "distributed": {
                                    "dist_count": "4"
                                    "transport": "tcp"
                                }
                                "replicated": {
                                    "replica_count": "3"
                                    "transport": "tcp"
                                }
                                "distributed-replicated": {
                                    "dist_count": "2"
                                    "replica_count": "3"
                                    "transport": "tcp"
                                }
                                "dispersed": {
                                    "disperse_count": "6"
                                    "redundancy_count": "2"
                                    "transport": "tcp"
                                }
                                "distributed-dispersed": {
                                    "dist_count": "2"
                                    "disperse_count": "6"
                                    "redundancy_count": "2"
                                    "transport": "tcp"
                                }
                                "arbiter": {
                                    "replica_count": "3"
                                    "arbiter_count": "1"
                                    "transport": "tcp"
                                }
                                "distributed-arbiter": {
                                    "dist_count": "2"
                                    "replica_count": "3"
                                    "arbiter_count": "1"
                                    "transport": "tcp"
                                }
               }
               
            }
        """   
        
        return cls.config_hashmap

    @classmethod
    def get_brick_root_list(cls, server_ip: str) -> list:
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
        brick_root_list = servers_info[server_ip]['brick_root']
        return brick_root_list
