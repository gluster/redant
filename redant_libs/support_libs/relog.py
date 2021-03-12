"""
Reading the name of the module itself would've given a good idea as to what
this module does ( kidding..relog is a bad name). So basically redant-log or
relog is responsible for wrapping around the base logging object and extending
it's functions to be used by the Redant framework.
"""
import logging
import logging.handlers


LOGGER = logging.getLogger(__name__)


# pylint: disable=W0603
class Logger:
    """
    The framework's logger class. It handles three levels of logging
    Info, Debug and Error. Having a has-a relationship curently with the logger
    object and wrapping it's functionalities.
    """
    log_function_mapping = {'I': LOGGER.info, 'D': LOGGER.debug,
                            'E': LOGGER.error}

    @staticmethod
    def set_logging_options(log_file_path: str = "/tmp/redant.log",
                            log_file_level: str = "I"):
        """
        This function is for configuring the logger
        """
        global LOGGER
        valid_log_level = ['I', 'D', 'E']
        log_level_dict = {'I': logging.INFO, 'D': logging.DEBUG,
                          'E': logging.ERROR}
        log_format = logging.Formatter("[%(asctime)s] %(levelname)s "
                                       "[%(module)s - %(lineno)s:%(funcName)s]"
                                       " - %(message)s")
        if log_file_level not in valid_log_level:
            print("Invalid log level given, Taking Log Level as Info.")
            log_file_level = 'I'
        LOGGER.setLevel(log_level_dict[log_file_level])
        log_file_handler = logging.handlers.WatchedFileHandler(log_file_path)
        log_file_handler.setFormatter(log_format)
        LOGGER.addHandler(log_file_handler)
        return LOGGER

    @classmethod
    def rlog(cls, log_message: str, log_level: str = 'I'):
        """
        Logger function used across the framework for logging.
        Created in a way so that people only have to deal with one
        single logger function istead of multiple as is the default
        manner.
        """
        cls.log_function_mapping[log_level](log_message)

    @staticmethod
    def get_logger_handle():
        """
        Getter function for logging.
        """
        return LOGGER
