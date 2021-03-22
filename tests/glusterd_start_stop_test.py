"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""


class TestCase:
    """
    The test case contains one function to test
    for glusterd service operations
    """

    def __init__(self, remote_exec: object):
        """
        This init function initializes the remote_exec
        class variable which is mixin object passed as a
        reference by runner_thread.
        Args:
            remote_exec (object): mixin object passed as reference.
        """
        self.remote_exec = remote_exec

    def gluster_start_stop_test(self):
        """
        The following steps are undertaken in the testcase:
        1) glusterd service is started on the server.
        4) glusterd service is stopped.
        """
        try:
            for _ in range(10):
                self.remote_exec.gluster_start("10.70.43.63")
                self.remote_exec.gluster_stop("10.70.43.63")
            print("Test Passed")

        except Exception as error:
            print(f"Test Failed:{error}")
