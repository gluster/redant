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
    def file_accessible(path, mode='r'):
        """
        Check if the file or directory at `path` can
        be accessed by the program using `mode` open flags.
        Args:

        """
        try:
            f = open(path, mode)
            f.close()
        except IOError:
            return False
        return True

    @staticmethod
    def generate_config_hashmap(filepath: str) -> dict:
        """
        Function to generate hashmap
        Args:
            filepath (str): Path for the config file.
        Rerturns:
            dict: Hashmap for config file as a dictionary.
            None: None on failure.
        """
        if not Parser.file_accessible(filepath):
            raise IOError
        configfd = open(filepath, 'r')
        config_hashmap = yaml.load(configfd, Loader=yaml.FullLoader)
        configfd.close()
        return config_hashmap
