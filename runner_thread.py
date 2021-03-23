"""
The thread runner is responsible for the execution of a given TC.
"""
import inspect
import importlib
import argparse
from redant_libs.redant_mixin import RedantMixin

if __name__ == "__main__":
    # Arguments passed bu the test runner for this TC.
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-c', '--conf_path', dest='conf_path',
                        help="Configuration file path",
                        default="/home/conf.yaml", type=str)
    PARSER.add_argument('-t', '--test_case_path', dest='tc_path',
                        help="Relative path of TC.", type=str)
    PARSER.add_argument('-tf', '--test_function', dest='test_fn',
                        help="Name of the test function to run", type=str)
    PARSER.add_argument('-l', '--log_path', dest='log_path',
                        help="Logfile path", default="/tmp/redant.log",
                        type=str)
    PARSER.add_argument('-ll', '--log_level', dest='log_level',
                        help="Log Level", default="I", type=str)
    ARGS = PARSER.parse_args()

    # the test case is loaded dynamically and it's members accessed.
    TC_MODULE_STR = ARGS.tc_path.replace("/", ".")[:-3]
    TC_MODULE = importlib.import_module(TC_MODULE_STR)
    TC_CLASS_STR = inspect.getmembers(TC_MODULE,
                                      inspect.isclass)[1][0]
    TC_CLASS = getattr(TC_MODULE, TC_CLASS_STR)
    TC_OBJ = TC_CLASS(client_list, server_list, log_path, log_level)
    RUN_TEST_FUNC = getattr(TC_OBJ, "run_test")
    TERMINATE_TEST_FUNC = getattr(TC_OBJ, "terminate")
    RUN_TEST_FUNC()
    TERMINATE_TEST_FUNC()

    if TC_OBJ.TEST_RES:
    #TODO: Proper test result collection
        print("The test passed")
    else:
        print("Test failed.")
