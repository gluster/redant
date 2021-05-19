"""
Migration script for test case migration from Glusto-tests to
redant repository. For more information, check the help flag.
"""

from os import path, system, chdir
import argparse


def check_paths(args) -> bool:
    """
    Validates the arguments
    """
    if not path.isfile(args.glustotc):
        return False

    if not path.isdir(args.rd):
        return False

    return True


def parse_args():
    """
    Function to create a command line parser.
    """
    parser = argparse.ArgumentParser(
        description='Redant test script migration script')
    parser.add_argument("-gl", "--glustotc",
                        help="Glusto TC path", action="store",
                        dest="glustotc", default=None, type=str,
                        required=True)
    parser.add_argument("-rd", "--redantdir",
                        help="Path for redant directory",
                        action="store", dest="rd", default=None, type=str,
                        required=True)
    return parser.parse_args()


def main():
    """
    I solemnly swear that the user would understand what is main.
    Pylint is sometimes too adamant and forces us to add things
    which one wouldn't want to.
    """
    args = parse_args()
    args.glustotc = path.abspath(args.glustotc)
    args.rd = path.abspath(args.rd)
    if not check_paths(args):
        return

    test_case_name = args.glustotc.split('/')[-1][:-3]
    system(f"mkdir -p /tmp/{test_case_name}")

    glusto_path_temp = args.glustotc.split('/')
    glusto_base_path = ""
    for pathseg in glusto_path_temp[1:-4]:
        glusto_base_path += (f"/{pathseg}")
    glusto_tc_path = "."
    for pathseg in glusto_path_temp[-4:]:
        glusto_tc_path += (f"/{pathseg}")

    chdir(glusto_base_path)

    cmd_to_run = (f"export reposrc={glusto_tc_path};git format-patch -o "
                  f"/tmp/{test_case_name} $(git log $reposrc|grep "
                  "^commit|tail -1|awk '{print $2}')^..HEAD $reposrc")
    system(cmd_to_run)
    chdir(args.rd)

    system(f"git am /tmp/{test_case_name}/*.patch")
    system(f"rm -rf /tmp/{test_case_name}")
    return


if __name__ == "__main__":
    main()
