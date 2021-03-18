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
            print("Test is running")

            server_ip1 = self.remote_exec.get_server_ip("server_vm1")
            server_ip2 = self.remote_exec.get_server_ip("server_vm2")
            flag = self.remote_exec.volume_create_force_option()

            self.remote_exec.gluster_start(server_ip1)

            self.remote_exec.peer_probe(server_ip2, server_ip1, force=flag)

            self.remote_exec.pool_list(server_ip1)

            self.remote_exec.peer_detach(server_ip1, server_ip2, force=flag)

            self.remote_exec.gluster_stop(server_ip1)

        except Exception as e:
            print(f"Test is failed:{e}")
