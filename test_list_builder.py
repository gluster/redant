"""

This component is responsible for creating a list
of tests-to-run to be used by the redant_test_runner component.
Input for this component : the tests-to-run list which was parsed
from the cli and the return: list of all the tests which are going
to be executed in the current session.

"""
import os
from comment_parser.comment_parser import extract_comments


class TestListBuilder:
    """
    The test list builder is concerned with parsing
    avialable TCs and their options so as to pass on the
    TC related data to the test_runner.
    """
    tests_to_run: list = []
    tests_run_dict: dict = {}

    @classmethod
    def create_test_dict(cls, path: str) -> dict:
        """
        This method creates a dict of TCs wrt the given directory
        path.
        Args:
            path (str): The directory path which contains the TCs
            to be run.
        Returns:
            A dict of the following format
            {
                "disruptive" : {
                                 1: {
                                      "volType" : [replicated,..],
                                      "modulePath" : "../test_sample.py",
                                    },
                                 2: {
                                       ...
                                    }
                               },
                "nonDisruptive" : {
                                    1: {
                                         "volType" : [replicated,..],
                                         "modulePath" : "../test_sample.py",
                                       },
                                    2: {
                                         ...
                                       }
                                  }
            }
        """
        # Obtaining list of paths to the TCs under given directory.
        try:
            for root, _, files in os.walk(path):
                for tfile in files:
                    if tfile.endswith(".py") and tfile.startswith("test"):
                        cls.tests_to_run.append(os.path.join(root, tfile))

        except Exception as e:
            print(e)
            return {}

        cls.tests_run_dict["disruptive"] = {}
        cls.tests_run_dict["nonDisruptive"] = {}
        disruptive_count = 0
        non_disruptive_count = 0
        # Extracting the test case flags.
        for test_case_path in cls.tests_to_run:
            test_flags = cls._get_test_module_info(test_case_path)
            if test_flags["tcNature"] == "disruptive":
                cls.tests_run_dict["disruptive"][disruptive_count] = {}
                cls.tests_run_dict["disruptive"][disruptive_count]["volType"]= test_flags["volType"]
                cls.tests_run_dict["disruptive"][disruptive_count]["modulePath"] = test_case_path
                disruptive_count += 1
            else:
                cls.tests_run_dict["nonDisruptive"][non_disruptive_count] = {}
                cls.tests_run_dict["nonDisruptive"][non_disruptive_count]["volType"] = test_flags["volType"]
                cls.tests_run_dict["nonDisruptive"][non_disruptive_count]["modulePath"] = test_case_path
                non_disruptive_count += 1
        return cls.tests_run_dict

    @classmethod
    def _get_test_module_info(cls, tc_path: str) -> dict:
        """
        This method gets the volume types for which the TC is to be run
        and the nature of a TC
        Args:
           tc_path (str): The path of the test case.

        Returns:
           test_flags (dict): This dictionary contains the volume types
                              for which the TC is to be run and the nature
                              of the TC, i.e. Disruptive / Non-Disruptive.
           For example,
                      {
                        "tcNature" : "disruptive",
                        "volType" : [replicated, ...]
                      }
        """
        flags = str(extract_comments(tc_path, mime="text/x-python")[0])
        tc_flags = {}
        tc_flags["tcNature"] = flags.split(';')[0]
        tc_flags["volType"] = flags.split(';')[1].split(',')

        return tc_flags
