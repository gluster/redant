"""

This component is responsible for creating a list
of tests-to-run to be used by the redant_test_runner component.
Input for this component : the tests-to-run list which was parsed
from the cli and the return: list of all the tests which are going
to be executed in the current session.

"""
import os


class TestListBuilder:
    """
    The test list builder is concerned with parsing
    avialable TCs and their options so as to pass on the
    TC related data to the test_runner.
    """
    tests_to_run: list = []

    @classmethod
    def create_test_list(cls, path: str) -> list:
        """
        This method creates a list of TCs wrt the given directory
        path.
        Args:
            path (str): The directory path which contains the TCs
            to be run.
        Returns:
            A list containing absolute paths of the TCs inside the
            given directory path.
        """
        try:

            for root, _, files in os.walk(path):
                for tfile in files:
                    if tfile.endswith(".py") and tfile.startswith("test"):
                        cls.tests_to_run.append(os.path.join(root, tfile))

        except Exception as e:
            print(e)

        return cls.tests_to_run

    @classmethod
    def get_test_module_info(cls, tc_path: str) -> dict:
        """
        This method instantiates the TC class object and stores the test
        function variables to be invoked in a list.
        """
        pass
