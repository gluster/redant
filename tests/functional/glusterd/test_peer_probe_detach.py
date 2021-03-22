"""
This component has a test-case for peers addition and deletion.
"""


class TestCase:
    """
    This TestCase class contains a function to test
    for peer probe , pool list and peer detach.
    """

    def __init__(self, redant: object):
        """
        This init function initializes the remote_exec
        class variable which is mixin object passed as a
        reference by runner_thread.
        Args:
            redant (object): mixin object passed as reference.
        """
        self.redant = redant

    def test_peer_probe_detach(self):
        """
        In this testcase:
        1) glusterd service is started
        2) peer probe of a server
        3) list the storage pool
        4) peer detach
        5) glusterd is stopped
        """
        try:

            self.redant.glusterd_start("192.168.122.220")

            self.redant.peer_probe("192.168.122.161", "192.168.122.220")

            self.redant.pool_list("192.168.122.220")

            self.redant.peer_detach("192.168.122.220", "192.168.122.161")

            self.redant.glusterd_stop("192.168.122.220")

        except Exception as e:
            print(f"Test is failed:{e}")
