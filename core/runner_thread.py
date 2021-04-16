"""
The thread runner is responsible for the execution of a given TC.
"""


class RunnerThread:
    """
    Runner thread will be encapsulating the functionalities for generically
    invoking a TC, creating the TC object and then invoking the required
    functions for running it.
    """

    def __init__(self, mname: str, tc_class, config_hashmap: dict,
                 volume_type: str, log_path: str, log_level: str):
        # Creating the test case object from the test case.
        self.tc_obj = tc_class(mname, config_hashmap, volume_type,
                               log_path, log_level)
        self.run_test_func = getattr(self.tc_obj, "parent_run_test")
        self.terminate_test_func = getattr(self.tc_obj, "terminate")
        self.test_stats = {
            'timeTaken': 0,
            'volType': volume_type
        }

    def run_thread(self):
        """
        Method to trigger the run test and the terminate test functions.
        """
        self.run_test_func()
        self.terminate_test_func()
        self.test_stats['testResult'] = self.tc_obj.TEST_RES
        return self.test_stats
