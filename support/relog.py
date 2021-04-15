"""
Reading the name of the module itself would've given a good idea as to what
this module does ( kidding..relog is a bad name). So basically redant-log or
relog is responsible for wrapping around the base logging object and extending
it's functions to be used by the Redant framework.
"""
import os
import logging
import logging.handlers
from datetime import datetime


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
        test_name = log_file_path.split('/')[-1:][0][:-4]
        self.logger.info(f'''
         ============================================================
                                         
           {test_name} started running: {datetime.now()}       
                                         
         ============================================================
        ''')

    @classmethod
    def log_dir_creation(cls, path: str, component_dict: dict,
                         test_dict: dict):
        """
        Module for Redant logg dir creation.
        Args:
            path (str): The directory path.
            component_dict (dict): The dict containing component lists
            example,
                   {
                     "functional" : ["component1", "component2", ...],
                     "performance" : ["component1", "component2", ...],
                     "example" : ["component1", "component2", ...]
                   }
            test_dict (dict): Dictionary containing list of TCs
            example,
                    {
                      "disruptive" : [
                                       {
                                         "volType" : ["volT1", "volT2",..],
                                         "modulePath" : "module_path",
                                         "moduleName" : "module_name",
                                         "componentName" : "component_name",
                                         "testClass" : "test_class",
                                         "testType" : "test_type"
                                       },
                                       {
                                           ...
                                       }
                                     ],
                     "nonDisruptive" : [
                                         {
                                           "volType" : ["volT1", "volT2",..],
                                           "modulePath" : "module_path",
                                           "moduleName" : "module_name",
                                           "componentName" : "component_name",
                                           "testClass" : "test_class",
                                           "testType" : "test_type"
                                         },
                                         {
                                             ...
                                         }
                                      ]
                   }
            Returns:
                None
        """
        if not os.path.isdir(path):
            os.makedirs(path)
        # Component wise directory creation.
        for test_type in component_dict:
            test_type_path = path+"/"+test_type
        if not os.path.isdir(test_type_path):
            os.makedirs(test_type_path)
        components = component_dict[test_type]
        for component in components:
            if not os.path.isdir(test_type_path+"/"+component):
                os.makedirs(test_type_path+"/"+component)
        # TC wise directory creation.
        for test in test_dict["disruptive"]:
            test_case_dir = path+"/"+test["modulePath"][5:-3]
            if not os.path.isdir(test_case_dir):
                os.makedirs(test_case_dir)
            for vol in test["volType"]:
                voltype_dir = test_case_dir+"/"+vol
                if not os.path.isdir(voltype_dir):
                    os.makedirs(voltype_dir)
        for test in test_dict["nonDisruptive"]:
            test_case_dir = path+"/"+test["modulePath"][5:-3]
            if not os.path.isdir(test_case_dir):
                os.makedirs(test_case_dir)
            for vol in test["volType"]:
                voltype_dir = test_case_dir+"/"+vol
                if not os.path.isdir(voltype_dir):
                    os.makedirs(voltype_dir)
