"""
This module takes care of:
1) Config file parsing (by gluster_test_parser).
2) Tests-to-run list preparation (by test_list_builder).
3) Invocation of the test_runner.
"""

import argparse
from parsing.redant_params_handler import ParamsHandler
from test_list_builder import TestListBuilder
from redant_test_runner import TestRunner

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
    parser.add_argument("-l", "--log-dir",
                        help="The directory wherein log will be stored.",
                        dest="log_fir", default="/tmp/redant", type=str)
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

    test_cases_dict = TestListBuilder.create_test_dict(args.test_dir)
   
    server_list = []
    client_list = []    

    # invoke the redant_test_runner
    TestRunner.init(test_cases_dict, server_list, client_list)
    TestRunner.run_tests()

    return 0


if __name__ == '__main__':
    main()
