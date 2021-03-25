"""
This module takes care of:
1) Config file parsing (by gluster_test_parser).
2) Tests-to-run list preparation (by test_list_builder).
3) Invocation of the test_runner.
"""

import os
import argparse
from core.parsing.params_handler import ParamsHandler
from core.test_list_builder import TestListBuilder
from core.test_runner import TestRunner
from result_handler import ResultHandler

def is_file_accessible(path: str, mode: str = 'r') -> bool:
    """
    To check if the given file is accessible or not
    so as to prevent parsing failures.
    Args:
        path (str): The file path whose accessibility is
                    to be checked.
        mode (str): The file access mode which would needs
                    to be validated for the given path.
    Returns:
        True: The file at the given path is accessible for
              the specified mode.
        False: The file is not accessible for the specified
               mode.
    """
    try:
        f = open(path, mode)
        f.close()
    except IOError:
        return False
    return True


def log_dir_check(path: str, component_dict: dict, test_dict: dict):
    """
    Sanity check function for redant logging directory.
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
    for test in test_dict["nonDisruptive"]:
        test_case_dir = path+"/"+test["modulePath"][5:-3]
        if not os.path.isdir(test_case_dir):
            os.makedirs(test_case_dir)


def pars_args():
    """
    Function to handle command line parsing for the redant.
    """

    parser = argparse.ArgumentParser(
        description='Redant test framework main script.')
    parser.add_argument("-c", "--config",
                        help="Config file(s) to read.",
                        action="store", dest="config_file",
                        default=None, type=str, required=True)
    parser.add_argument("-t", "--test-dir",
                        help="The test directory where TC(s) exist",
                        dest="test_dir", default=None, type=str, required=True)
    parser.add_argument("-sp", "--specific-test-path",
                        help="Path of the specific test to be run from tests/",
                        dest="spec_test", default=None, type=str,
                        required=False)
    parser.add_argument("-l", "--log-dir",
                        help="The directory wherein log will be stored.",
                        dest="log_dir", default="/tmp/redant", type=str)
    parser.add_argument("-ll", "--log-level",
                        help="The log level.",
                        dest="log_level", default="I", type=str)
    parser.add_argument("-cc", "--concurrency-count",
                        help="Number of concurrent test runs",
                        dest="semaphore_count", default=4, type=int)
    return parser.parse_args()


def main():
    """
    Invocation order being.
    1. Parsing the command line arguments.
    2. Parsing the config file to get the configuration details.
    3. Invoking the test_list_builder to build the TC run order.
    4. Passing the details to the test_runner.
    """
    args = pars_args()

    if is_file_accessible(args.config_file):
        ParamsHandler.get_config_hashmap(args.config_file)
    else:
        print(f"The config file at {args.config_file} is not accessible.")
        return -1

    # Obtain the client and server dict.
    mach_conn_dict = ParamsHandler.get_nodes_info()

    # Building the test list and obtaining the TC details.
    test_cases_tuple = TestListBuilder.create_test_dict(args.test_dir)
    test_cases_dict = test_cases_tuple[0]
    test_cases_component = test_cases_tuple[1]

    # Creating log dirs.
    log_dir_check(args.log_dir, test_cases_component, test_cases_dict)

    # Pre test run test list builder is modified.
    test_cases_dict = TestListBuilder.pre_test_run_list_modify(test_cases_dict)

    # invoke the test_runner.
    TestRunner.init(test_cases_dict, mach_conn_dict, args.log_dir,
                    args.log_level, args.semaphore_count)
    all_test_results = TestRunner.run_tests()

    ResultHandler.display_test_results(all_test_results)

    return 0


if __name__ == '__main__':
    main()
