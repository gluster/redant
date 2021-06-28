"""
This module consists a single class - Parser,which
parses the configuration file given the filepath.
"""
import yaml


class Parser:
    """
    This class consists an API which parses the
    configuration file from the filepath. The
    API is called from the ParamsHandler module.
    """

    @staticmethod
    def generate_config_hashmap(filepath: str) -> dict:
        """
        Function to generate hashmap
        Args:
            filepath (str): Path for the config file.
        Rerturns:
            dict: Hashmap for config file as a dictionary.
        """
        with open(filepath, 'r') as configfd:
            config_hashmap = yaml.load(configfd, Loader=yaml.SafeLoader)
        return config_hashmap
