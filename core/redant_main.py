"""
This module takes care of:
1) Config file parsing (by gluster_test_parser).
2) Tests-to-run list preparation (by test_list_builder).
3) Invocation of the test_runner.
"""

import sys
import argparse
from core.parsing.params_handler import ParamsHandler
from core.test_list_builder import TestListBuilder
from core.test_runner import TestRunner
from result_handler import ResultHandler
import time

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
                        dest="spec_test", action='store_true', required=False)
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

    start = time.time()
    args = pars_args()

    ParamsHandler.get_config_hashmap(args.config_file)

    # Obtain the client and server dict.
    mach_conn_dict = ParamsHandler.get_nodes_info()

    # Building the test list and obtaining the TC details.
    test_cases_tuple = TestListBuilder.create_test_dict(args.test_dir,
                                                        args.spec_test)
    test_cases_dict = test_cases_tuple[0]
    test_cases_component = test_cases_tuple[1]

    # Creating log dirs.
    sys.path.insert(1, ".")
    from support.ops.support_ops.relog import Logger
    Logger.log_dir_creation(args.log_dir, test_cases_component,
                            test_cases_dict)

    # Pre test run test list builder is modified.
    test_cases_dict = TestListBuilder.pre_test_run_list_modify(test_cases_dict)

    # invoke the test_runner.
    TestRunner.init(test_cases_dict, mach_conn_dict, args.log_dir,
                    args.log_level, args.semaphore_count)
    all_test_results = TestRunner.run_tests()

    ResultHandler.display_test_results(all_test_results)

    print(f"\nTotal time taken by the framework: {time.time()-start} sec")



if __name__ == '__main__':
    main()
