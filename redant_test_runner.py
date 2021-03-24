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
    def init(cls, test_run_dict, mach_conn_dict, base_log_path="/tmp"):
        cls.test_run_dict = test_run_dict
        cls.mach_conn_dict = mach_conn_dict

    @classmethod
    def run_tests(cls):
        # TODO add logic to parse the test_run_dict to run tests.
        # Currently for testing the logical flow, hardcoding the calls
        # Running non-disruptive cases first.
        for test in cls.test_run_dict["nonDisruptive"]:
            tc_class = cls.test_run_dict["nonDisruptive"][test]["testClass"]
            runner_thread_obj = RunnerThread(tc_class,
                                             cls.mach_conn_dict["clients"],
                                             cls.mach_conn_dict["servers"],
                                             "/tmp/redant.log", 'I')
            value = runner_thread_obj.run_thread()
            print(value)
        for test in cls.test_run_dict["disruptive"]:
            tc_class = cls.test_run_dict["disruptive"][test]["testClass"]
            runner_thread_obj = RunnerThread(tc_class,
                                             cls.mach_conn_dict["clients"],
                                             cls.mach_conn_dict["servers"],
                                             "/tmp/redant.log", 'I')
            value = runner_thread_obj.run_thread()
            print(value)
