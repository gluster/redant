"""
The thread runner is responsible for the execution of a given TC.
"""

from redant_libs.support_libs.relog import Logging
from redant_libs.support_libs.rexe import Rexe
import argparse

if __name__ == "__main__":
    # Test runner passes the arguments which are paramount for running a specific TC.
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf_path', dest='conf_path', help="Configuration file path",
                        default="/home/conf.yaml", type=str)
    parser.add_argument('-t', '--test_case_path', dest='tc_path', help="Path of the test case to be run", type=str)
    parser.add_argument('-l', '--log_path', dest='log_path', help="Logfile path",
                        default="/tmp/redant.log", type=str)
    parser.add_argument('-ll', '--log_level', dest='log_level', help="Log Level",
                        default="I", type=str)
    args = parser.parse_args()

    # Create the logger object.
    logger = Logging.set_logging_options(args.log_path, args.log_level)

    # Create remote connection with the servers and clients.
    logger.debug("Creating the remote connection")
    remote_executor = Rexe(args.conf_path)
    remote_executor.establish_connection()

