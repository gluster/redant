"""
This file contains a test-case which tests glusterd
starting and stopping of glusterd service.
"""
# disruptive;

from tests.abstract_test import AbstractTest


class TestCase(AbstractTest):
    """
    The test case contains one function to test
    for glusterd service operations
    """

    def run_test(self, redant):
        """
        The following steps are undertaken in the testcase:
        1) glusterd service is started on the server.
        2) glusterd service is stopped.
        """
        for _ in range(5):
            redant.stop_glusterd(self.server_list)
            redant.start_glusterd(self.server_list)
