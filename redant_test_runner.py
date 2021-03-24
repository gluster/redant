"""
The test runner is responsible for handling the list of TCs
to be run and invoking them.
"""
import uuid
from colorama import Fore, Style
from runner_thread import RunnerThread

class TestRunner:
    """
    Test runner class will encapsulate the functionalities corresponding
    to the invocation of the runner threads with respect to the list
    created by the test list builder.
    """

    @classmethod
    def init(cls, test_run_dict: dict, mach_conn_dict: dict,
             base_log_path: str, log_level: str):
        cls.test_run_dict = test_run_dict
        cls.mach_conn_dict = mach_conn_dict
        cls.base_log_path = base_log_path
        cls.log_level = log_level

    @classmethod
    def run_tests(cls):
        # TODO Concurrency to be added based on the test types.
        for test in cls.test_run_dict["nonDisruptive"]:
            print(test)
            tc_class = test["testClass"]
            for volume in test["volType"]:
                tc_log_path = cls.base_log_path+test["modulePath"][5:-3]+"/"+\
                    test["moduleName"][:-3]+"-"+volume+".log"
                runner_thread_obj = RunnerThread(str(uuid.uuid1().int), tc_class,
                                                 cls.mach_conn_dict["clients"],
                                                 cls.mach_conn_dict["servers"],
                                                 volume, tc_log_path,
                                                 cls.log_level)
                value = runner_thread_obj.run_thread()
                result_text = test["moduleName"][:-3]+"-"+volume
                if value:
                    result_text += " FAIL"
                    print(Fore.RED + result_text)
                    print(Style.RESET_ALL)
        for test in cls.test_run_dict["disruptive"]:
            tc_class = test["testClass"]
            for volume in test["volType"]:
                tc_log_path = cls.base_log_path + test["modulePath"][5:-3]+"/"+\
                    test["moduleName"][:-3]+"-"+volume+".log"
                runner_thread_obj = RunnerThread(str(uuid.uuid1().int), tc_class,
                                                 cls.mach_conn_dict["clients"],
                                                 cls.mach_conn_dict["servers"],
                                                 volume, tc_log_path,
                                                 cls.log_level)
                value = runner_thread_obj.run_thread()
                result_text = test["moduleName"][:-3]+"-"+volume
                if value:
                    result_text += " PASS"
                    print(Fore.GREEN + result_text)
                    print(Style.RESET_ALL)
