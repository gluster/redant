"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""
#disruptive;

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
        for _ in range(10):
            self.redant.start_glusterd(self.server_list)
            self.redant.stop_glusterd(self.server_list)
