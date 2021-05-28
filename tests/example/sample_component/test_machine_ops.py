"""
Sample test for showing how machine ops can be handled.
"""
# disruptive;

from tests.d_parent_test import DParentTest


class TestCase(DParentTest):
    """
    The test case is for testing out the machine ops.
    """

    def run_test(self, redant):
        """
        The purpose of this test case is to check the machine ops
        operations.
        """
        redant.check_node_power_status(self.server_list)
        redant.reboot_nodes(self.server_list[0])
        redant.check_node_power_status(self.server_list)

        ret = redant.wait_node_power_up(self.server_list[0])
        if not ret:
            raise Exception(f"{self.server_list[0]} is offline")

        ret = redant.wait_till_all_peers_connected(self.server_list)
        if not ret:
            raise Exception(f"{self.server_list} are not in connected state")
