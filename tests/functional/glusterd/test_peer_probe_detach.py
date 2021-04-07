"""
This component has a test-case for peers addition and deletion.
"""
#disruptive;dist,rep,arb,disp,dist-rep,dist-arb

from tests.parent_test import ParentTest


class TestCase(ParentTest):
    """
    This TestCase class contains a function to test
    for peer probe , pool list and peer detach.
    """

    def run_test(self):
        """
        In this testcase:
        1) glusterd service is started
        2) peer probe of a server
        3) list the storage pool
        4) peer detach
        5) glusterd is stopped
        """
        try:
            server1 = self.server_list[0]
            server2 = self.server_list[1]

            self.redant.peer_probe(server2, server1)

            self.redant.pool_list(server1)

            self.redant.peer_detach(server1, server2)
            
            server_list = [server1,server2]
            self.redant.create_cluster(server_list)

        except Exception as e:
            self.TEST_RES = False
            print(f"Test is failed:{e}")
