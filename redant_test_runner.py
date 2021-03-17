"""
This module is the gluster_test_main module which
takes care of:
1) Config file parsing (by gluster_test_parser).
2) Tests-to-run list preparation (by test_list_builder).
3) Invocation of the runner_thread which runs the testcase.
"""

import argparse
from parsing.redant_params_handler import ParamsHandler


def pars_args():
    """Parse arguments with argparse module
    """

    parser = argparse.ArgumentParser(
        description='Create config hashmap based on config file')
    parser.add_argument("-c", "--config",
                        help="Config file(s) to read.",
                        action="store", dest="config_file",
                        default=None)
    return parser.parse_args()


def main():
    """
    All the apis for the required functions will be called here
    """
    args = pars_args()

    if args.config_file:
        ParamsHandler.get_config_hashmap(args.config_file)


if __name__ == '__main__':
    main()
