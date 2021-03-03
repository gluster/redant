from rexe.rexe import Rexe as R
from rexe.rexe import (
    set_logging_options,
    logger
)
import logging
import logging.handlers

class Redant_Resources:
        
    """
    For testing purpose this class is added
    """
    
    def __init__(self, log_file_path, log_file_level):

        set_logging_options(log_file_level=log_file_level,log_file_path=log_file_path)

