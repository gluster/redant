"""
This file contains a test-case which tests
volume operations like creation and deletion
"""
#disruptive;dist,rep,arb,disp

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    The test case contains one function to test
    for volume creation and deletion
    """

    def run_test(self):
        """
        The following steps are undertaken in the testcase:
        1) glusterd service is started on the server.
        2) Volume is created on the server node.
        3) Volume is deleted on the server node.
        4) glusterd service is stopped.
        """
        try:
            server = self.server_list[0]

            self.redant.start_glusterd(server)

            self.redant.volume_create(server, "test-vol",
                                      [f"{server}:/brick1"],
                                      force=True)
            self.redant.volume_delete(server, "test-vol")

            self.redant.stop_glusterd(server)
            print("Test Passed")

        except Exception as error:
            self.TEST_RES = False
            print(f"Test Failed:{error}")
