"""
Sample test for showing how special glusterd operations can be handled.
"""
# nonDisruptive;dist

from tests.nd_parent_test import NdParentTest


class TestCase(NdParentTest):
    """
    The test case to test glusterd service operations
    """

    def run_test(self, redant):
        """
        The purpose of this test case is for verifying the glusterd
        operations.
        """
        ret = redant.get_state(self.server_list[0])
        redant.logger.info(f"Gluster state at node {self.server_list[0]} is"
                           f" {ret}")
