"""
Reading the name of the module itself would've given a good idea as to what
this module does ( kidding..relog is a bad name). So basically redant-log or
relog is responsible for wrapping around the base logging object and extending
it's functions to be used by the Redant framework.
"""
import os
import logging
import logging.handlers


class Logger(logging.Logger):
    """
    The framework's logger class. It handles three levels of logging
    Info, Debug and Error.
    """

    def get_test_log_dir(self, log_file_path: str) -> str:
        """
        Method to obtain the absolute path for the parent dir of a
        test case.
        """
        demarcation_index = log_file_path.rfind("/")
        return log_file_path[:demarcation_index]

    def init_logger(self, mname: str, log_file_path: str,
                    log_file_level: str = "I"):
        """
        This function is for configuring the logger
        """
        self.logger = logging.getLogger(mname)
        valid_log_level = ['I', 'D', 'E']
        log_level_dict = {'I': logging.INFO, 'D': logging.DEBUG,
                          'E': logging.ERROR}
        log_format = logging.Formatter("[%(asctime)s] %(levelname)s "
                                       "[%(filename)s:%(lineno)d:"
                                       "%(funcName)s] - %(message)s")
        if log_file_level not in valid_log_level:
            print("Log level indicator should be one of %s, "
                  "falling back to I (Info)." % ','.join(valid_log_level))
            log_file_level = 'I'
        self.logger.setLevel(log_level_dict[log_file_level])
        test_log_dir = self.get_test_log_dir(log_file_path)
        if not os.path.isdir(test_log_dir):
            os.makedirs(test_log_dir)
        log_file_handler = logging.handlers.WatchedFileHandler(log_file_path)
        log_file_handler.setFormatter(log_format)
        self.logger.addHandler(log_file_handler)

    @classmethod
    def log_dir_creation(cls, parent_path: str, test_path_list: list):
        """
        Module for Redant logg dir creation.
        Args:
            parent_path (str): The parent log directory path.
            test_path_list (list)
        Returns:
            None
        """
        if not os.path.isdir(parent_path):
            os.makedirs(parent_path)

        for test_path in test_path_list:
            dir_creation_path = f"{parent_path}/{test_path[6:-3]}"
            if not os.path.isdir(dir_creation_path):
                os.makedirs(dir_creation_path)
