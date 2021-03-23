"""
This file contains a test-case which tests
volume operations like creation and deletion
"""
#nonDisruptive;dist,rep,arb,disp

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    The test case contains one function to test
    for volume creation and deletion
    """

    def volume_create_delete_test(self):
        """
        The following steps are undertaken in the testcase:
        1) glusterd service is started on the server.
        2) Volume is created on the server node.
        3) Volume is deleted on the server node.
        4) glusterd service is stopped.
        """
        try:

            self.redant.gluster_start("10.70.43.63")

            self.redant.volume_create("10.70.43.63", "test-vol",
                                      ["10.70.43.63:/brick1"],
                                      force=True)
            self.redant.volume_delete("10.70.43.63", "test-vol")

            self.redant.gluster_stop("10.70.43.63")
            print("Test Passed")

        except Exception as error:
            print(f"Test Failed:{error}")
