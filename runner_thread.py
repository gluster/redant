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

    # Creating mixin class and initializing logging and rexe parameters.
    RE_MIXIN = RedantMixin(ARGS.conf_path)
    RE_MIXIN.set_logging_options(ARGS.log_path, ARGS.log_level)
    RE_MIXIN.establish_connection()

    # the test case is loaded dynamically and it's members accessed.
    TC_MODULE_STR = ARGS.tc_path.replace("/", ".").strip(".py")
    TC_MODULE = importlib.import_module(TC_MODULE_STR)
    TC_CLASS_STR = inspect.getmembers(TC_MODULE,
                                      inspect.isclass)[0][0]
    TC_CLASS = getattr(TC_MODULE, TC_CLASS_STR)
    TC_OBJ = TC_CLASS(RE_MIXIN)
    TC_FUNC_STR = ARGS.test_fn
    TC_FUNC = getattr(TC_OBJ, TC_FUNC_STR)
    TC_FUNC()
