"""
The test runner is responsible for handling the list of TCs
to be run and invoking them.
"""
import uuid
import time
from datetime import datetime
from multiprocessing import Process, Queue
from colorama import Fore, Style
from runner_thread import RunnerThread


class TestRunner:
    """
    Test runner class will encapsulate the functionalities corresponding
    to the invocation of the runner threads with respect to the list
    created by the test list builder.
    """

    @classmethod
    def init(cls, test_run_dict: dict, param_obj: dict,
             base_log_path: str, log_level: str, multiprocess_count: int):
        cls.test_results = {}
        cls.param_obj = param_obj
        cls.concur_count = multiprocess_count
        cls.base_log_path = base_log_path
        cls.log_level = log_level
        cls.concur_test = test_run_dict["nonDisruptive"]
        cls.non_concur_test = test_run_dict["disruptive"]
        cls.threadList = []
        cls.job_result_queue = Queue()
        cls.nd_job_queue = Queue()
        cls._prepare_thread_tests()

    @classmethod
    def run_tests(cls):
        """
        The non-disruptive tests are invoked followed by the disruptive
        tests.
        """
        jobs = []
        if bool(cls.concur_count):
            for iter in range(cls.concur_count):
                proc = Process(target=cls._worker_process,
                               args=(cls.nd_job_queue,))
                jobs.append(proc)
                proc.start()

            # TODO replace incremental backup with a signalling and lock.
            backoff_time = 0
            while len(jobs) > 0:
                jobs = [job for job in jobs if job.is_alive()]
                if backoff_time == 20:
                    time.sleep(backoff_time)
                else:
                   backoff_time += 1

            for iter in range(cls.concur_count):
                proc.join()

        for test in cls.non_concur_test:
            cls.test_results[test['moduleName'][:-3]] = []
            cls._run_test(test)

        return cls.job_result_queue

    @classmethod
    def _prepare_thread_tests(cls):
        """
        This method creates the threadlist for non disruptive tests
        """
        for test in cls.concur_test:
            cls.test_results[test['moduleName'][:-3]] = []
            cls.nd_job_queue.put(test)
        
    @classmethod
    def _run_test(cls, test_dict: dict, thread_flag: bool=False):
        """
        A generic method handling the run of both disruptive and non
        disruptive tests.
        """
        tc_class = test_dict["testClass"]
        tc_log_path = cls.base_log_path+test_dict["modulePath"][5:-3]+"/" +\
            test_dict["volType"]+"/"+test_dict["moduleName"][:-3]+".log"

        # to calculate time spent to execute the test
        start = time.time()
        runner_thread_obj = RunnerThread(tc_class, cls.param_obj,
                                         test_dict["moduleName"][:-3],
                                         test_dict["volType"], tc_log_path,
                                         cls.log_level, thread_flag)
        test_stats = runner_thread_obj.run_thread()

        test_stats['timeTaken'] = time.time() - start
        result_text = test_dict["moduleName"][:-3]+"-"+test_dict["volType"]
        if test_stats['testResult']:
            test_stats['testResult'] = "PASS"
            result_text += " PASS"
            print(Fore.GREEN + result_text)
            print(Style.RESET_ALL)
        else:
            result_text += " FAIL"
            test_stats['testResult'] = "FAIL"
            print(Fore.RED + result_text)
            print(Style.RESET_ALL)

        cls.test_results[test_dict["moduleName"][:-3]].append(test_stats)
        result_value = { test_dict["moduleName"][:-3] : test_stats }
        cls.job_result_queue.put(result_value)

    @classmethod
    def _worker_process(cls, nd_queue):
        """
        Worker process would be taking up new jobs from the queue
        till the queue is empty. This queue will consist only non disruptive
        test cases.
        """
        while not nd_queue.empty():
            job_data = nd_queue.get()
            cls._run_test(job_data, True)
