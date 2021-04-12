"""
This component has a test-case for peers probe
and detach operations.
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
        redant.create_cluster(self.server_list)
        redant.pool_list(server1)
        redant.peer_detach(server1, server2)
        redant.peer_detach(server2, server2)
