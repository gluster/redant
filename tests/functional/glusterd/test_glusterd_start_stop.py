"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""
#nonDisruptive;dist,rep,arb,disp

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    The test case contains one function to test
    for glusterd service operations
    """

    def run_test(self):
        """
        The following steps are undertaken in the testcase:
        1) glusterd service is started on the server.
        4) glusterd service is stopped.
        """
        server = self.server_list[0]
        try:
            for _ in range(10):
                self.redant.glusterd_start(server)
                self.redant.glusterd_stop(server)
            print("Test Passed")

        except Exception as error:
            print(f"Test Failed:{error}")
