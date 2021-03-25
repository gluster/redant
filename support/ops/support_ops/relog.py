"""
Reading the name of the module itself would've given a good idea as to what
this module does ( kidding..relog is a bad name). So basically redant-log or
relog is responsible for wrapping around the base logging object and extending
it's functions to be used by the Redant framework.
"""
import logging
import logging.handlers


class Logger(logging.Logger):
    """
    The framework's logger class. It handles three levels of logging
    Info, Debug and Error.
    """

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
                                       "[%(module)s - %(lineno)s:%(funcName)s]"
                                       " - %(message)s")
        if log_file_level not in valid_log_level:
            print("Invalid log level given, Taking Log Level as Info.")
            log_file_level = 'I'
        self.logger.setLevel(log_level_dict[log_file_level])
        log_file_handler = logging.handlers.WatchedFileHandler(log_file_path)
        log_file_handler.setFormatter(log_format)
        self.logger.addHandler(log_file_handler)
        self.log_function_mapping = {'I': self.logger.info,
                                     'D': self.logger.debug,
                                     'E': self.logger.error}

    def rlog(self, log_message: str, log_level: str = 'I'):
        """
        Logger function used across the framework for logging.
        Created in a way so that people only have to deal with one
        single logger function istead of multiple as is the default
        manner.
        """
        self.log_function_mapping[log_level](log_message)
