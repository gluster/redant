"""

This component is responsible for creating a list
of tests-to-run to be used by the test_runner component.
Input for this component : the tests-to-run list which was parsed
from the cli and the return: list of all the tests which are going
to be executed in the current session.

"""
import os
import inspect
import importlib
import copy
import sys
from comment_parser.comment_parser import extract_comments


valid_vol_types = ['rep', 'dist', 'arb', 'disp', 'dist-rep', 'dist-arb',
                   'dist-disp', "Generic"]


class TestListBuilder:
    """
    The test list builder is concerned with parsing
    avialable TCs and their options so as to pass on the
    TC related data to the test_runner.
    """
    excluded_tests: list = []
    tests_path_list = []
    r_ndtest_list = []
    dt_ndtest_list = []
    dtr_ndtest_list = []
    a_ndtest_list = []
    dta_ndtest_list = []
    ds_ndtest_list = []
    dtds_ndtest_list = []
    gen_ndtest_list = []
    dtest_list = []
    test_nd_volc_dict = {}
    test_nd_vold_dict = {}
    nd_category = {'rep': r_ndtest_list, 'dist': dt_ndtest_list,
                   'arb': a_ndtest_list, 'disp': ds_ndtest_list,
                   'dist-rep': dtr_ndtest_list, 'dist-arb': dta_ndtest_list,
                   'dist-disp': dtds_ndtest_list, 'Generic': gen_ndtest_list}

    @classmethod
    def create_test_dict(cls, path: str, excluded_tests: list,
                         single_tc: bool = False):
        """
        This method creates a dict of TCs wrt the given directory
        path.
        Args:
            path (str): The directory path which contains the TCs
            to be run.
            single_tc (bool): If the user wants to run a single TC instead
            of the complete suite.
        Returns:
        """
        def path_error_handler(exception_instance):
            raise FileNotFoundError

        global valid_vol_types
        # Obtaining list of paths to the TCs under given directory.
        if not single_tc:
            if path not in excluded_tests:
                for root, _, files in os.walk(path,
                                              onerror=path_error_handler):
                    if root not in excluded_tests:
                        for tfile in files:
                            if tfile.endswith(".py") and \
                               tfile.startswith("test"):
                                test_case_path = os.path.join(root, tfile)
                                if test_case_path not in excluded_tests:
                                    cls.tests_path_list.append(test_case_path)

        elif path not in excluded_tests:
            cls.tests_path_list.append(path)

        # Extracting the test case flags and adding module level info.
        for test_case_path in cls.tests_path_list:
            test_flags = cls._get_test_module_info(test_case_path)
            test_dict = {}
            test_dict["modulePath"] = test_case_path
            test_dict["moduleName"] = test_case_path.split("/")[-1]
            test_dict["componentName"] = test_case_path.split("/")[-2]
            test_dict["testClass"] = cls._get_test_class(test_case_path)
            test_dict["testType"] = test_case_path.split("/")[-3]
            test_dict["tcNature"] = test_flags["tcNature"]
            if test_flags["tcNature"] == "disruptive":
                for vol_type in test_flags["volType"]:
                    if vol_type not in valid_vol_types:
                        raise Exception(f"{test_dict['modulePath']} has"
                                        f" invalid volume type {vol_type}")
                    temp_test_dict = copy.deepcopy(test_dict)
                    temp_test_dict["volType"] = copy.deepcopy(vol_type)
                    cls.dtest_list.append(temp_test_dict)
            elif test_flags["tcNature"] == "nonDisruptive":
                for vol_type in test_flags["volType"]:
                    if vol_type not in valid_vol_types:
                        raise Exception(f"{test_dict['modulePath']} has"
                                        f" invalid volume type {vol_type}")
                    temp_test_dict = copy.deepcopy(test_dict)
                    cls.nd_category[vol_type].append(temp_test_dict)
            else:
                raise Exception(f"Invalid test nature : "
                                f" {test_flags['tcNature']}")

        cls.spec_vol = []
        nd_tests_count = 0
        for (vol_t, listv) in cls.nd_category.items():
            if vol_t == "Generic":
                continue
            nd_tests_count += len(listv)
            if single_tc and len(listv) != 0:
                cls.spec_vol.append(vol_t)
        if nd_tests_count > 0:
            cls._create_nd_special_tests()

    @classmethod
    def get_spec_vol_types(cls):
        """
        Method to obtain the list of volume types for which this
        specifc test has to run.
        Returns:
            list
        """
        return cls.spec_vol

    @classmethod
    def _create_nd_special_tests(cls):
        """
        Method to create the test dictionary for the special
        tests, create and destroy volume which are used for
        non Disruptive test cases.
        """
        special_paths = ['tests/vol_create_test.py',
                         'tests/vol_destroy_test.py']
        for path in special_paths:
            special_nd = {}
            special_nd['modulePath'] = path
            special_nd['moduleName'] = path.split("/")[-1]
            special_nd['testClass'] = cls._get_test_class(path)
            special_nd['tcNature'] = 's'
            if cls.test_nd_volc_dict == {}:
                cls.test_nd_volc_dict = special_nd
            else:
                cls.test_nd_vold_dict = special_nd

    @classmethod
    def get_special_tests_dict(cls) -> list:
        """
        Method to get special tests dictionary.
        """
        if cls.test_nd_volc_dict == {}:
            return []
        return [cls.test_nd_volc_dict, cls.test_nd_vold_dict]

    @classmethod
    def get_test_path_list(cls) -> list:
        """
        Method to return the list of test case paths.
        Return:
            list of test case paths.
        """
        return cls.tests_path_list

    @classmethod
    def get_dtest_list(cls) -> list:
        """
        Method to return the dtest_list.
        Returns:
            dtest_list
        """
        return cls.dtest_list

    @classmethod
    def get_ndtest_list(cls, vol_type: str) -> list:
        """
        Method to return ndtest_list of a volume type
        as requested.
        Arg:
            vol_type (list)
        Returns:
            *_ndtest_list (list)
        """
        global valid_vol_types
        if vol_type not in valid_vol_types:
            return []
        return cls.nd_category[vol_type]

    @classmethod
    def get_nd_tests_count(cls) -> int:
        """
        Method to obtain a count of nd tests.
        Returns integer value.
        """
        global valid_vol_types
        count = 0
        for vol_type in valid_vol_types:
            count += len(cls.nd_category[vol_type])
        return count

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
        tc_flags["tcNature"] = flags.split(';')[0].strip()
        tc_flags["volType"] = flags.split(';')[1].split(',')
        if tc_flags["volType"] == ['']:
            tc_flags["volType"] = ["Generic"]
        return tc_flags

    @classmethod
    def _get_test_class(cls, tc_path: str):
        """
        Method to import the module and inspect the class to be stored
        for creating objects later.
        """
        tc_module_str = tc_path.replace("/", ".")[:-3]
        sys.path.insert(1, ".")
        tc_module = importlib.import_module(tc_module_str)
        tc_class_str = inspect.getmembers(tc_module,
                                          inspect.isclass)[1][0]
        tc_class = getattr(tc_module, tc_class_str)
        return tc_class
