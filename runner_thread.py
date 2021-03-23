"""
The thread runner is responsible for the execution of a given TC.
"""

class RunnerThread:
    """
    Runner thread will be encapsulating the functionalities for generically
    invoking a TC, creating the TC object and then invoking the required
    functions for running it.
    """
    def __init__(self, tc_class, client_list, server_list, log_path,
                 log_level):
        # Creating the test case object from the test case.
        self.tc_obj = tc_class(client_list, server_list, log_path, log_level)
        self.run_test_func = getattr(self.tc_obj, "run_test")
        self.terminate_test_func = getattr(self.tc_obj, "terminate")

    def run_thread(self):
        """
        Method to trigger the run test and the terminate test functions.
        """
        self.run_test_func()
        self.terminate_test_func()
        return self.tc_obj.TEST_RES
