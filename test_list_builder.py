"""

This component is responsible for creating a list
of tests-to-run to be used by the redant_test_runner component.
Input for this component : the tests-to-run list which was parsed
from the cli and the return: list of all the tests which are going
to be executed in the current session.

"""
import os
import glob


class TestListBuilder:
    """
    This class contains create_test_list
    which helps in creeting a list of
    tests that has to be run
    """

    @classmethod
    def create_test_list(cls, dir_path: list) -> list:
        """
        This function creates a list of test cases
        that are going to be executed and returns
        the same.
        """
        tests_to_run: list = []

        try:

            for path in dir_path:
                abs_dir_path: str = os.path.abspath(path)

                if not abs_dir_path.endswith(".py"):
                    list_of_files: list = glob.glob(f"{abs_dir_path}/*.py")

                    tests_to_run.extend(list_of_files)
                else:
                    tests_to_run.extend([abs_dir_path])

        except Exception as e:
            print(e)

        return tests_to_run
