"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""


class TestCase:
    """
    The test case contains one function to test
    for glusterd service operations
    """

    def __init__(self, redant: object):
        """
        This init function initializes the redant
        class variable which is mixin object passed as a
        reference by runner_thread.
        Args:
            redant (object): mixin object passed as reference.
                             Point of contact for the redant
                             framework.
        """
        self.redant = redant

    def gluster_start_stop_test(self):
        """
        The following steps are undertaken in the testcase:
        1) glusterd service is started on the server.
        4) glusterd service is stopped.
        """
        try:
            for _ in range(10):
                self.redant.gluster_start("10.70.43.63")
                self.redant.gluster_stop("10.70.43.63")
            print("Test Passed")

        except Exception as error:
            print(f"Test Failed:{error}")
