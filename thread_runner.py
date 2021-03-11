"""
The thread runner is responsible for the execution of a given TC.
"""
import inspect
import importlib
import argparse
from redant_libs.support_libs.relog import Logger
from redant_libs.support_libs.rexe import Rexe

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

    # Create the logger object.
    logger = Logger.set_logging_options(args.log_path, args.log_level)

    # Create remote connection with the servers and clients.
    Logger.rlog("Creating the remote connection", 'D')
    remote_executor = Rexe(args.conf_path)
    remote_executor.establish_connection()

    # Load the test case function to be called.
    module_name = args.tc_path.replace("/", ".").strip(".py")
    module = importlib.import_module(module_name)
    test_class_str = inspect.getmembers(module, inspect.isclass)[0][0]

    # The test function is imported.
    test_class = getattr(module, test_class_str)
    test_object = test_class(remote_executor) 
    test_func_str = args.test_fn
    test_func = getattr(test_object, test_func_str)
    test_func()
