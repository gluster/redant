"""
This component has a test-case for peers addition and deletion.
"""


class TestCase:
    """
    This TestCase class contains a function to test
    for peer probe , pool list and peer detach.
    """

<<<<<<< HEAD
    def __init__(self, redant: object):
=======
    def __init__(self, remote_exec: object):
>>>>>>> 9691f337663ede960f44098182729f4466c64b6b
        """
        This init function initializes the remote_exec
        class variable which is mixin object passed as a
        reference by runner_thread.
        Args:
<<<<<<< HEAD
            redant (object): mixin object passed as reference.
        """
        self.redant = redant
=======
            remote_exec (object): mixin object passed as reference.
        """
        self.remote_exec = remote_exec
>>>>>>> 9691f337663ede960f44098182729f4466c64b6b

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

<<<<<<< HEAD
            self.redant.glusterd_start("192.168.122.220")

            self.redant.peer_probe(
                "192.168.122.161", "192.168.122.220")

            self.redant.pool_list("192.168.122.220")

            self.redant.peer_detach(
                "192.168.122.220", "192.168.122.161")

            self.redant.glusterd_stop("192.168.122.220")
=======
            self.remote_exec.glusterd_start("192.168.122.220")

            self.remote_exec.peer_probe(
                "192.168.122.161", "192.168.122.220")

            self.remote_exec.pool_list("192.168.122.220")

            self.remote_exec.peer_detach(
                "192.168.122.220", "192.168.122.161")

            self.remote_exec.glusterd_stop("192.168.122.220")
>>>>>>> 9691f337663ede960f44098182729f4466c64b6b

        except Exception as e:
            print(f"Test is failed:{e}")
