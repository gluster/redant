"""
The thread runner is responsible for the execution of a given TC.
"""
import inspect
import importlib
import argparse
from redant_libs.redant_mixin import redant_mixin

if __name__ == "__main__":
    # Test runner passes the arguments which are paramount for running a specific TC.
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf_path', dest='conf_path', help="Configuration file path",
                        default="/home/conf.yaml", type=str)
    parser.add_argument('-t', '--test_case_path', dest='tc_path', help="Path of the test case to be run from tests directory. Start with tests/", type=str)
    parser.add_argument('-tf', '--test_function', dest='test_fn', help="Name of the test function to run", type=str)
    parser.add_argument('-l', '--log_path', dest='log_path', help="Logfile path",
                        default="/tmp/redant.log", type=str)
    parser.add_argument('-ll', '--log_level', dest='log_level', help="Log Level",
                        default="I", type=str)
    args = parser.parse_args()

    # Creating mixin class and initializing logging and rexe parameters.
    re_mixin = redant_mixin(args.conf_path)
    re_mixin.set_logging_options(args.log_path, args.log_level)
    re_mixin.establish_connection()

    # the test case is loaded dynamically and it's members accessed.
    test_case_module_name = args.tc_path.replace("/", ".").strip(".py")
    test_case_module = importlib.import_module(test_case_module_name)
    test_class_str = inspect.getmembers(test_case_module, inspect.isclass)[0][0]
    test_class = getattr(test_case_module, test_class_str)
    test_object = test_class(re_mixin) 
    test_func_str = args.test_fn
    test_func = getattr(test_object, test_func_str)
    test_func()
