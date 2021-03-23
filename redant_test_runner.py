"""
The test runner is responsible for handling the list of TCs
to be run and invoking them.
"""
from runner_thread import RunnerThread

class TestRunner:
    """
    Test runner class will encapsulate the functionalities corresponding
    to the invocation of the runner threads with respect to the list
    created by the test list builder.
    """

    @classmethod
    def init(cls, test_run_dict, server_list, client_list, base_log_path="/tmp"):
        cls.test_run_dict = test_run_dict
        cls.server_list = server_list
        cls.client_list = client_list

    @classmethod
    def run_tests(cls):
        # TODO add logic to parse the test_run_dict to run tests.
        # Currently for testing the logical flow, hardcoding the calls
        # Running non-disruptive cases first.
        for test in cls.test_run_dict["nonDisruptive"]:
            tc_class = cls.test_run_dict["nonDisruptive"][test]["testClass"]
            runner_thread_obj = RunnerThread(tc_class, cls.client_list,
                                             cls.server_list, "/tmp", 'I')
            print(cls.test_run_dict["nonDisruptive"][test])
        for test in cls.test_run_dict["disruptive"]:
            tc_class = cls.test_run_dict["disruptive"][test]["testClass"]
            runner_thread_obj = RunnerThread(tc_class, cls.client_list,
                                             cls.server_list, "/tmp", 'I')
            print(cls.test_run_dict["disruptive"][test])
        #runner_thread_obj = RunnerThread(cls.tst_run_dict[
