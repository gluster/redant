"""
The test runner is responsible for handling the list of TCs
to be run and invoking them.
"""
import time
from multiprocessing import Process, Queue
from halo import Halo
from runner_thread import RunnerThread


class TestRunner:
    """
    Test runner class will encapsulate the functionalities corresponding
    to the invocation of the runner threads with respect to the list
    created by the test list builder.
    """

    @classmethod
    def init(cls, TestListBuilder, param_obj, fmwk_obj, base_log_path: str,
             log_level: str, multiprocess_count: int, spec_test: bool):
        """
        Test runner intialization.
        Args:
            TestListBuilder (class)
            param_obj (object)
            base_log_path (str)
            log_level (str)
            multiprocess_count (int)
            spec_test (bool) True if only one test is run.
        """
        cls.param_obj = param_obj
        cls.concur_count = multiprocess_count
        cls.base_log_path = base_log_path
        cls.log_level = log_level
        cls.threadList = []
        cls.get_dtest_fn = TestListBuilder.get_dtest_list
        cls.get_ndtest_fn = TestListBuilder.get_ndtest_list
        cls.get_snd_test_fn = TestListBuilder.get_special_tests_dict
        cls.get_spec_vol_types_fn = TestListBuilder.get_spec_vol_types
        cls.nd_tests_count = TestListBuilder.get_nd_tests_count()
        cls.logger = fmwk_obj.get_framework_logger()
        cls.logger.info("Creating thread queues for the tests")
        cls._prepare_thread_queues(spec_test)

    @classmethod
    def _prepare_thread_queues(cls, spec_test: bool):
        """
        This method creates the requisite queues for the test run.
        Arg:
            spec_test (bool) True if only one test is to be run.
        """
        cls.job_result_queue = Queue()
        cls.r_nd_jobq = Queue()
        cls.dt_nd_jobq = Queue()
        cls.a_nd_jobq = Queue()
        cls.ds_nd_jobq = Queue()
        cls.dtr_nd_jobq = Queue()
        cls.dta_nd_jobq = Queue()
        cls.dtds_nd_jobq = Queue()
        cls.gen_nd_jobq = Queue()
        cls.nd_vol_queue = Queue()
        vol_types = ['rep', 'dist', 'disp', 'arb', 'dist-rep', 'dist-disp',
                     'dist-arb']
        cls.queue_map = {'arb': cls.a_nd_jobq, 'disp': cls.ds_nd_jobq,
                         'dist-rep': cls.dtr_nd_jobq, 'rep': cls.r_nd_jobq,
                         'dist-arb': cls.dta_nd_jobq, 'dist': cls.dt_nd_jobq,
                         'dist-disp': cls.dtds_nd_jobq}

        # Get special tests dict
        special_test_dict = cls.get_snd_test_fn()

        if special_test_dict != []:
            # When a single test is ran
            if spec_test:
                spec_vols = cls.get_spec_vol_types_fn()
                if spec_vols == []:
                    vol_types = []
                else:
                    vol_types = spec_vols

            for vol_type in vol_types:
                cls.queue_map[vol_type].put(special_test_dict[0])

            for vol_type in vol_types:
                cls.nd_vol_queue.put(vol_type)
                for test in cls.get_ndtest_fn(vol_type):
                    cls.queue_map[vol_type].put(test)

            for vol_type in vol_types:
                cls.queue_map[vol_type].put(special_test_dict[1])

        # Populating the generic queue.
        for test in cls.get_ndtest_fn('Generic'):
            cls.gen_nd_jobq.put(test)

    @classmethod
    def _nd_worker_process(cls, vol_queue, queue_map, gen_nd_jobq, ):
        """
        Worker process has two set of queue hierarchy to deal with.
        It picks up a volume type from the volume queue and then
        starts picking off jobs specific to that particular volume. Once, the
        jobs related to this volume ends, it picks up a new volume to work
        with. Once a worker find the vol queue as empty, it goes ahead and
        starts working with Generic cases.
        Args:
            vol_queue (Queue) : Queue containing volume types of gluster.
            queue_map (Dict) : A dictionary mapping volume types to sub queues
                               for given volume type.
            gen_nd_jobq (Queue) : Queue containing jobs for Generic
                                  non disruptive cases.
        """
        while not vol_queue.empty():
            job_vol = vol_queue.get()
            cls.logger.info(f"Worker picked up job_volume {job_vol}")
            job_queue = queue_map[job_vol]
            while not job_queue.empty():
                job_data = job_queue.get()
                cls.logger.info(f"Worker picked up job {job_data}")
                job_data['volType'] = job_vol
                cls._run_test(job_data)

        if gen_nd_jobq.qsize() != 0:
            while not gen_nd_jobq.empty():
                job_data = gen_nd_jobq.get()
                cls.logger.info(f"Worker picked up job {job_data}")
                job_data['volType'] = "Generic"
                cls._run_test(job_data)

    @classmethod
    def run_tests(cls, env_obj):
        """
        The test runs are of three stages,
        1. Stage 1 is for non disruptive test cases which can run in the
           concurrent flow and can use a pre-existing volume or don't
           even need a pre-existing volume ( psst. Generic cases ).
        3. Stage 2 is the run of Disruptive test cases.
        """
        cls.env_obj = env_obj
        # Stage 1
        jobs = []
        if bool(cls.nd_tests_count):
            cls.logger.info("Starting Non Disruptive test case runs.")
            for _ in range(cls.concur_count):
                proc = Process(target=cls._nd_worker_process,
                               args=(cls.nd_vol_queue, cls.queue_map,
                                     cls.gen_nd_jobq,))
                jobs.append(proc)
                proc.start()

            # TODO replace sleep with a signalling and lock.
            while len(jobs) > 0:
                jobs = [job for job in jobs if job.is_alive()]
                time.sleep(1)

            for _ in range(cls.concur_count):
                proc.join()

        # Stage 2
        if cls.get_dtest_fn():
            cls.logger.info("Starting Disruptive test case runs.")
            for test in cls.get_dtest_fn():
                cls._run_test(test)

        # Because of the infinitesimal delay in value being reflected in Queue
        # it was found that sometimes the Queue which was empty had been given
        # some value, it still showed itself as empty.
        # TODO: Handle it without sleep.
        itr = 0
        while itr < 5:
            if cls.job_result_queue.empty():
                time.sleep(1)
            else:
                break
            itr += 1

        cls.logger.info("Finished test executions.")
        return cls.job_result_queue

    @classmethod
    def _run_test(cls, test_dict: dict):
        """
        A generic method handling the run of both disruptive and non
        disruptive tests.
        """

        spinner = Halo(spinner='dots', text_color='yellow')
        tc_class = test_dict["testClass"]
        volume_type = test_dict["volType"]
        mname = test_dict["moduleName"][:-3]

        tc_log_path = (f"{cls.base_log_path+test_dict['modulePath'][5:-3]}/"
                       f"{volume_type}/{mname}.log")

        # to calculate time spent to execute the test
        start = time.time()

        spinner.succeed(text=f"Running test case : {mname}-{volume_type}")
        runner_thread_obj = RunnerThread(tc_class, cls.param_obj, volume_type,
                                         mname, cls.logger, cls.env_obj,
                                         tc_log_path, cls.log_level)

        test_stats = runner_thread_obj.run_thread()

        test_stats['timeTaken'] = time.time() - start
        test_stats['tcNature'] = test_dict['tcNature']
        spinner.clear()
        result_text = f"{test_dict['moduleName'][:-3]}-{test_dict['volType']}"
        if test_stats['testResult'][0] is True:
            test_stats['testResult'] = "PASS"
            result_text += " PASS"
            spinner = Halo(spinner='dots', text_color='green')
            spinner.succeed(text=f"{mname}-{volume_type} Succeeded")
        elif test_stats['testResult'][0] is False:
            result_text += " FAIL"
            test_stats['testResult'] = "FAIL"
            spinner = Halo(spinner='dots', text_color='red')
            spinner.fail(f"{mname}-{volume_type} Failed")
        else:
            result_text += " SKIP"
            test_stats['testResult'] = "SKIP"
            spinner = Halo(spinner='dots', text_color='cyan')
            spinner.info(f"{mname}-{volume_type} SKIP")
        test_stats['component'] = tc_log_path.split('/')[-4]

        result_value = {test_dict["moduleName"][:-3]: test_stats}
        cls.job_result_queue.put(result_value)
