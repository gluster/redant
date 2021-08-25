"""
This module takes care of:
1) Config file parsing (by gluster_test_parser).
2) Tests-to-run list preparation (by test_list_builder).
3) Invocation of the test_runner.
"""
import os
import sys
import time
import datetime
import traceback
import argparse
import pyfiglet
from halo import Halo
from environ import environ, FrameworkEnv
from parsing.params_handler import ParamsHandler
from test_list_builder import TestListBuilder
from test_runner import TestRunner
from result_handler import handle_results
from common.relog import Logger
sys.path.insert(1, ".")
sys.path.insert(1, "./common")


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
                        dest="log_dir", default="/tmp/redant", type=str)
    parser.add_argument("-ll", "--log-level",
                        help="The log level. Default log level is Info",
                        dest="log_level", default="I", type=str)
    parser.add_argument("-cc", "--concurrency-count",
                        help="Number of concurrent test runs. Default is 2.",
                        dest="concur_count", default=2, type=int)
    parser.add_argument("-xls", "--excel-sheet",
                        help="Spreadsheet for result. Default value is NULL",
                        dest="excel_sheet", default=None, type=str)
    parser.add_argument("--show-backtrace",
                        help="Show full backtrace on error",
                        dest="show_backtrace", action='store_true')
    parser.add_argument("-kold", "--keep-old-logs",
                        help="Don't clear the old glusterfs logs directory "
                        "during environment setup",
                        dest="keep_logs", action='store_true')
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

    if args.show_backtrace:
        def errer(exc, msg=None):
            raise exc
    else:
        def errer(exc, msg=None):
            if not msg:
                msg = "error: {exc}"
            print(msg.format(exc=exc), file=sys.stderr)
            sys.exit(1)

    spinner = Halo(spinner='dots')
    spinner.start("Starting param handling")
    try:
        param_obj = ParamsHandler(args.config_file)
    except OSError as e:
        spinner.fail("error in param handling")
        errer(e, "Error on loading config file: {exc}")
    spinner.succeed("Param Handling Success.")

    spinner.start("Building test list")
    # Building the test list and obtaining the TC details.
    excluded_result = param_obj.get_excluded_tests()
    if not excluded_result[1]:
        spinner.fail("Error in exclude list. Invalid path present")
        sys.exit(1)

    excluded_tests = excluded_result[0]
    spec_test = (args.test_dir.endswith(".py")
                 and args.test_dir.split("/")[-1].startswith("test"))
    try:
        TestListBuilder.create_test_dict(args.test_dir, excluded_tests,
                                         spec_test)
    except FileNotFoundError as e:
        spinner.fail("FileNotFoundError in test list builder")
        errer(e, "Error: Can't find the file")
    spinner.succeed("Test List built")

    spinner.start("Creating log dirs")
    # Creating log dirs.
    current_time_rep = str(datetime.datetime.now())
    log_dir_current = f"{args.log_dir}/{current_time_rep}"
    Logger.log_dir_creation(
        log_dir_current, TestListBuilder.get_test_path_list())
    latest = 'latest'
    tmplink = f"{args.log_dir}/{latest}.{current_time_rep}"
    os.symlink(current_time_rep, tmplink)
    os.rename(tmplink, f"{args.log_dir}/{latest}")
    spinner.succeed("Log dir creation successful.")

    # Framework Environment datastructure.
    env_obj = FrameworkEnv()
    env_obj.init_ds()

    # Environment setup.
    env_set = environ(param_obj, env_obj, errer, f"{log_dir_current}/main.log",
                      args.log_level)
    logger_obj = env_set.get_framework_logger()
    logger_obj.debug("Running env setup.")
    env_set.setup_env(args.keep_logs)

    # invoke the test_runner.
    logger_obj.debug("Running the test cases.")
    TestRunner.init(TestListBuilder, param_obj, env_set, log_dir_current,
                    args.log_level, args.concur_count, spec_test)
    result_queue = TestRunner.run_tests(env_obj)
    logger_obj.debug("Collected test results queue.")

    # Environment cleanup. TBD.
    total_time = time.time() - start

    # Setup the result
    if args.excel_sheet is None:
        handle_results(result_queue, total_time, logger_obj)
    else:
        handle_results(result_queue, total_time, logger_obj,
                       args.excel_sheet)

    logger_obj.debug("Starting env teardown.")
    env_set.teardown_env()


if __name__ == '__main__':
    print(pyfiglet.figlet_format("REDANT", font="slant"))
    failure = False
    try:
        main()
    except Exception as error:
        error_string = str(error)
        tb = traceback.format_exc()
        error_string = f"{error_string}. Traceback : {tb}"
        failure = True

    if failure:
        time_now = time.time()
        try:
            f = open(f"/tmp/redant/redant-{time_now}", 'w')
            f.write(error_string)
            f.close()
            print(f"Traceback put into /tmp/redant/redant-{time_now}")
        except Exception as err:
            print(f"Couldn't write main exception {error_string} due to {err}")
