"""
The thread runner is responsible for the execution of a given TC.
"""

import traceback


class RunnerThread:
    """
    Runner thread will be encapsulating the functionalities for generically
    invoking a TC, creating the TC object and then invoking the required
    functions for running it.
    """

    def __init__(self, tc_class, param_obj, volume_type: str,
                 mname: str, logger_obj, env_obj, log_path: str,
                 log_level: str):
        # Creating the test case object from the test case.
        self.logger = logger_obj
        self.tname = (f"{mname}-{volume_type}")
        self.tc_obj = tc_class(
            mname, param_obj, volume_type, env_obj, log_path, log_level)
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
        self.logger.info(f"Running {self.tname}")
        try:
            self.run_test_func()
            self.terminate_test_func()
            self.test_stats['testResult'] = self.tc_obj.TEST_RES
        except Exception as error:
            tb = traceback.format_exc()
            self.logger.error(f"{self.tname} : {error}")
            self.logger.error(f"{self.tname} : {tb}")
            self.test_stats['testResult'] = False
        return self.test_stats
