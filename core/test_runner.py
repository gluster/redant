"""
The test runner is responsible for handling the list of TCs
to be run and invoking them.
"""
import uuid
from colorama import Fore, Style
from runner_thread import RunnerThread
from threading import Thread, Semaphore
import time

class TestRunner:
    """
    Test runner class will encapsulate the functionalities corresponding
    to the invocation of the runner threads with respect to the list
    created by the test list builder.
    """

    @classmethod
    def init(cls, test_run_dict: dict, mach_conn_dict: dict,
             base_log_path: str, log_level: str, semaphore_count: int):
        cls.mach_conn_dict = mach_conn_dict
        cls.semaphore = Semaphore(semaphore_count)
        cls.base_log_path = base_log_path
        cls.log_level = log_level
        cls.concur_test = test_run_dict["nonDisruptive"]
        cls.non_concur_test = test_run_dict["disruptive"]
        cls.threadList = []
        cls.test_results = {}
        cls._prepare_thread_tests()

    @classmethod
    def run_tests(cls):
        """
        The non-disruptive tests are invoked followed by the disruptive
        tests.
        """
        for test_thread in cls.threadList:
            test_thread.start()
        for test_thread in cls.threadList:
            test_thread.join()
        thread_flag = False
        
        for test in cls.non_concur_test:
        
            cls.test_results[test['moduleName'][:-3]] = []
        
        for test in cls.non_concur_test:
            
            test_res = cls._run_test(test, thread_flag)
            cls.test_results[test['moduleName'][:-3]].append(test_res)

        return cls.test_results

    @classmethod
    def _prepare_thread_tests(cls):
        """
        This method creates the threadlist for non disruptive tests
        """
        thread_flag = True
        
        for test in cls.concur_test:
        
            cls.test_results[test['moduleName'][:-3]] = []
        
        for test in cls.concur_test:
            cls.test_results[test['moduleName'][:-3]].append({
                'volType': test['volType'],
                'timeTaken': 0,
                'testResult':'PASS'
            })
            cls.threadList.append(Thread(target=cls._run_test,
                                         args=(test, thread_flag,)))

    @classmethod
    def _run_test(cls, test_dict: dict, thread_flag: bool):
        """
        A generic method handling the run of both disruptive and non
        disruptive tests.
        """
        if thread_flag:
            cls.semaphore.acquire()
        tc_class = test_dict["testClass"]
        tc_log_path = cls.base_log_path+test_dict["modulePath"][5:-3]+"/" +\
            test_dict["moduleName"][:-3]+"-"+test_dict["volType"]\
            + ".log"
        
        # to calculate time spent to execute the test
        start = time.time()
        runner_thread_obj = RunnerThread(str(uuid.uuid1().int), tc_class,
                                         cls.mach_conn_dict["clients"],
                                         cls.mach_conn_dict["servers"],
                                         test_dict["volType"], tc_log_path,
                                         cls.log_level, test_dict["moduleName"][:-3])
        test_result = runner_thread_obj.run_thread()
        
        test_result['timeTaken'] = time.time() - start
        result_text = test_dict["moduleName"][:-3]+"-"+test_dict["volType"]
        if test_result['testResult']:
            test_result['testResult'] = "PASS"
            result_text += " PASS"
            print(Fore.GREEN + result_text)
            print(Style.RESET_ALL)
        else:
            result_text += " FAIL"
            test_result['testResult'] = "FAIL"
            print(Fore.RED + result_text)
            print(Style.RESET_ALL)
        if thread_flag:
            cls.semaphore.release()

        return test_result