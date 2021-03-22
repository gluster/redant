"""
This component has a test-case for peers addition and deletion.
"""


class testcase:
    """
    This TestCase class contains a function to test
    for peer probe , pool list and peer detach.
    """

    def __init__(self, remote_exec: object):
        """
        This init function initializes the remote_exec
        class variable which is mixin object passed as a
        reference by runner_thread.
        Args:
            remote_exec (object): mixin object passed as reference.
        """
        self.remote_exec = remote_exec

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

            self.remote_exec.gluster_start("192.168.122.220")

            self.remote_exec.peer_probe(
                "192.168.122.161", "192.168.122.220", force=True)

            self.remote_exec.pool_list("192.168.122.220")

            self.remote_exec.peer_detach(
                "192.168.122.220", "192.168.122.161", force=True)

            self.remote_exec.gluster_stop("192.168.122.220")

        except Exception as e:
            print(f"Test is failed:{e}")
