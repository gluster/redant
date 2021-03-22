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
    This class contains create_test_list
    which helps in creeting a list of
    tests that has to be run
    """
    tests_to_run: list = []

    @classmethod
    def create_test_list(cls, path: str) -> list:
        """
        This function creates a list of test cases
        that are going to be executed and returns
        the same.
        """
        try:

            for root, _, files in os.walk(path):
                for tfile in files:
                    if tfile.endswith(".py") and tfile.startswith("test"):
                        cls.tests_to_run.append(os.path.join(root, tfile))

        except Exception as e:
            print(e)

        return cls.tests_to_run
