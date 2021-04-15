"""
This component has a test-case for testing
peer related operations
"""
#disruptive;

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    This TestCase class contains a function to test
    for peer probe , pool list and peer detach.
    """

    def run_test(self, redant):
        """
        In this testcase:
        1) Cluster is created.
        2) The storage pool is listed.
        3) The cluster is destroyed ( currently with the help of peer detach)
        """
        server1 = self.server_list[0]
        server2 = self.server_list[1]
        server3 = self.server_list[2]
        redant.create_cluster(self.server_list)
        redant.pool_list(server1)
        redant.peer_detach(server1, server2)
        redant.peer_detach(server3, server2)
