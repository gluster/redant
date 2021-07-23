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

    def __init__(self, filepath: str):
        """
        Parsing the config file.
        """
        self.config_hashmap = Parser.generate_config_hashmap(filepath)
        self.server_config = self.config_hashmap['servers_info']
        self.client_config = self.config_hashmap['clients_info']
        self.volume_types = self.config_hashmap['volume_types']

    def get_server_ip_list(self) -> list:
        """
        Gives the list of all server ip
        Returns:
            list: list of all server ip address
        """
        return list(self.server_config.keys())

    def get_server_config(self) -> dict:
        """
        Getter for server config details.
        Returns:
            dict: Server config details.
        """
        return self.server_config

    def get_client_config(self) -> dict:
        """
        Getter for client config details.
        Returns:
            dict: Client config details.
        """
        return self.client_config

    def get_client_ip_list(self) -> list:
        """
        Gives the list of all client ip
        Returns:
            list: list of all client ip address
        """
        return list(self.client_config.keys())

    def get_volume_types(self) -> dict:
        """
        Getter for volume information.
        Retuns:
            Dict
        """
        return self.volume_types

    def get_config_hashmap(self) -> dict:
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
                                "dist": {
                                    "dist_count": "4"
                                    "transport": "tcp"
                                }
                                "rep": {
                                    "replica_count": "3"
                                    "transport": "tcp"
                                }
                                "dist-rep": {
                                    "dist_count": "2"
                                    "replica_count": "3"
                                    "transport": "tcp"
                                }
                                "disp": {
                                    "disperse_count": "6"
                                    "redundancy_count": "2"
                                    "transport": "tcp"
                                }
                                "dist-disp": {
                                    "dist_count": "2"
                                    "disperse_count": "6"
                                    "redundancy_count": "2"
                                    "transport": "tcp"
                                }
                                "arb": {
                                    "replica_count": "3"
                                    "arbiter_count": "1"
                                    "transport": "tcp"
                                }
                                "dist-arb": {
                                    "dist_count": "2"
                                    "replica_count": "3"
                                    "arbiter_count": "1"
                                    "transport": "tcp"
                                }
               }

            }
        """
        return self.config_hashmap

    def get_brick_root_list(self, server_ip: str) -> list:
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
        return self.server_config[server_ip]['brick_root']

    # TODO: Handling servers with multiple brick roots.
    def get_brick_roots(self) -> dict:
        """
        Get the mapping of server ip to their brick roots
        Returns:
           Dict
        TODO: Update the values in the dict to be a list of bricks, instead
              of the first brick of the list.
        """
        brick_roots = {}
        for server in self.server_config:
            brick_roots[server] = self.server_config[server]['brick_root']
        return brick_roots

    def get_excluded_tests(self):
        """
        Gets a list of exluded tests from the config file.
        Returns:
            list : list of exluded tests
        """
        return self.config_hashmap.get("excluded_tests", [])
